from ultralytics import YOLO
import cv2 as cv
import cvzone
import numpy as np
import psycopg2
from datetime import datetime
import os
import random

def init_db_schema():
    conn = psycopg2.connect(
        dbname="AccidentDB", 
        user="postgres", 
        password="dadmom2004", 
        host="localhost", 
        port="5432"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='accident_reports' AND column_name='camera_name'
            ) THEN
                ALTER TABLE accident_reports ADD COLUMN camera_name TEXT;
            END IF;
        END $$;
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Initialize database schema
init_db_schema()

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="AccidentDB", 
    user="postgres", 
    password="dadmom2004", 
    host="localhost", 
    port="5432"
)
cursor = conn.cursor()

# YOLOv8 model
model = YOLO("/Users/pr9teen/Documents/GitHub/epics 2/runs/detect/train/weights/best.pt")

# Video setup
video_path = "/Users/pr9teen/Documents/GitHub/epics 2/videos_accidents/V9.mp4"
vid = cv.VideoCapture(video_path)

# Video details
fps = int(vid.get(cv.CAP_PROP_FPS))
width = int(vid.get(cv.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT))

# Output video
output_path = "/Users/pr9teen/Documents/GitHub/epics 2/runs/detect/predict4.mp4"
fourcc = cv.VideoWriter_fourcc(*'mp4v')
out = cv.VideoWriter(output_path, fourcc, fps, (width, height))

# Create directory for snapshots
snapshot_dir = "static/accident_snapshots"
os.makedirs(snapshot_dir, exist_ok=True)

# Available camera IDs and locations
camera_locations = [
    {"id": 1, "lat": 23.0775, "lon": 76.8513, "name": "Main Gate"},
    {"id": 2, "lat": 23.0778, "lon": 76.8515, "name": "Parking Lot"},
    {"id": 3, "lat": 23.0773, "lon": 76.8510, "name": "Building Entrance"}
]

# Accident detection state
accident_detected = False
cooldown_frames = 1500
cooldown_counter = 0

try:
    while True:
        ret, frame = vid.read()
        if not ret:
            break

        results = model(frame, stream=True)
        accident_in_frame = False

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0].item()

                if confidence > 0.3:
                    accident_in_frame = True
                    cvzone.cornerRect(frame, (x1, y1, x2 - x1, y2 - y1), colorR=(0, 0, 255), l=3)
                    cv.putText(frame, f'Accident {confidence:.2f}', (x1, y1 - 10),
                              cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                    if not accident_detected:
                        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                        snapshot_filename = f"{snapshot_dir}/accident_{timestamp}.jpg"
                        cv.imwrite(snapshot_filename, frame)
                        
                        # Randomly select a camera
                        camera = random.choice(camera_locations)
                        
                        try:
                            insert_query = """
                            INSERT INTO accident_reports 
                            (timestamp, cctv_id, latitude, longitude, severity, snapshot_path, camera_name) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id;
                            """
                            cursor.execute(insert_query, (
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                camera['id'],
                                camera['lat'],
                                camera['lon'],
                                'Minor',
                                snapshot_filename,
                                camera['name']
                            ))
                            accident_id = cursor.fetchone()[0]
                            conn.commit()
                            
                            print(f"Accident {accident_id} recorded at {timestamp}")
                            accident_detected = True
                            cooldown_counter = cooldown_frames
                        except Exception as e:
                            print(f"Database error: {e}")
                            conn.rollback()

        if cooldown_counter > 0:
            cooldown_counter -= 1
        else:
            accident_detected = False

        cv.imshow("YOLOv8 Detection", frame)
        out.write(frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    vid.release()
    out.release()
    cv.destroyAllWindows()
    cursor.close()
    conn.close()
    print(f"Processing complete! Video saved at: {output_path}")