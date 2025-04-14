from flask import Flask, render_template, request, jsonify
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)

TOTAL_POLICE = 50

def get_db_connection():
    return psycopg2.connect(
        dbname="AccidentDB",
        user="postgres",
        password="dadmom2004",
        host="localhost",
        port="5432"
    )

def get_available_police():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(police_count), 0) FROM accident_reports 
        WHERE police_deployed = TRUE AND confirmed_by_hq = FALSE
    """)
    deployed_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return TOTAL_POLICE - deployed_count

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, timestamp, cctv_id, latitude, longitude, severity, 
               snapshot_path, police_deployed, police_count, confirmed_by_hq
        FROM accident_reports
        WHERE confirmed_by_hq = FALSE
        ORDER BY timestamp DESC
    """)
    accidents = cur.fetchall()
    
    cur.execute("""
        SELECT id, timestamp, cctv_id, police_count, confirmed_by_hq
        FROM accident_reports
        WHERE police_deployed = TRUE
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    deployment_logs = cur.fetchall()
    
    cur.close()
    conn.close()
    
    available_police = get_available_police()
    
    return render_template(
        'dashboard.html',
        accidents=accidents,
        deployment_logs=deployment_logs,
        available_police=available_police,
        total_police=TOTAL_POLICE
    )

@app.route('/deploy_police', methods=['POST'])
def deploy_police():
    accident_id = request.form.get('accident_id')
    police_count = int(request.form.get('police_count', 1))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        available = get_available_police()
        if available < police_count:
            return jsonify({
                'status': 'error',
                'message': f'Only {available} police units available (requested {police_count})'
            }), 400
        
        cur.execute("""
            UPDATE accident_reports
            SET police_deployed = TRUE, police_count = %s
            WHERE id = %s AND police_deployed = FALSE
            RETURNING id, cctv_id, police_count;
        """, (police_count, accident_id))
        
        result = cur.fetchone()
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'Police already deployed to this accident'
            }), 400
        
        conn.commit()
        available = get_available_police()
        
        return jsonify({
            'status': 'success',
            'accident_id': result[0],
            'cctv_id': result[1],
            'police_count': result[2],
            'available_police': available
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        cur.close()
        conn.close()

@app.route('/confirm_hq', methods=['POST'])
def confirm_hq():
    accident_id = request.form.get('accident_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT police_count FROM accident_reports
            WHERE id = %s AND police_deployed = TRUE AND confirmed_by_hq = FALSE
        """, (accident_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'No active police deployment found for this accident'
            }), 400
        
        police_count = result[0]
        
        cur.execute("""
            UPDATE accident_reports
            SET confirmed_by_hq = TRUE
            WHERE id = %s
            RETURNING id, cctv_id, police_count;
        """, (accident_id,))
        
        result = cur.fetchone()
        conn.commit()
        available = get_available_police()
        
        return jsonify({
            'status': 'success',
            'accident_id': result[0],
            'cctv_id': result[1],
            'police_freed': result[2],
            'available_police': available
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    os.makedirs('static/accident_snapshots', exist_ok=True)
    app.run(debug=True, port=5001)