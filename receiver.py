import cv2
import socket
import pickle
import struct
from ultralytics import YOLO
import psycopg2
from datetime import datetime

# PostgreSQL Connection
conn = psycopg2.connect(
    dbname="AccidentDB", 
    user="postgres", 
    password="dadmom2004", 
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Load YOLOv8 Model
model = YOLO("/Users/pr9teen/epics 2/runs/detect/train/weights/best.pt")

# Socket Setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '172.25.237.140'  # Replace with friend's local IP (e.g., 192.168.x.x)
port = 9999
client_socket.connect((host_ip, port))

# Accident Detection Logic
accident_detected = False
cooldown_frames = 1500
cooldown_counter = 0

data = b""
payload_size = struct.calcsize("Q")

while True:
    while len(data) < payload_size:
        packet = client_socket.recv(4 * 1024)  # 4KB buffer
        if not packet:
            break
        data += packet
    
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]
    
    while len(data) < msg_size:
        data += client_socket.recv(4 * 1024)
    
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame_data)

    # Process frame with YOLOv8
    results = model(frame, stream=True)
    accident_in_frame = False

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0].item()
            if confidence > 0.3:
                accident_in_frame = True
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f'Accident {confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                if not accident_detected:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        INSERT INTO Accident_Reports 
                        (timestamp, cctv_id, latitude, longitude, severity) 
                        VALUES (%s, %s, %s, %s, 'Minor')
                    """, (timestamp, 1, 28.7041, 77.1025))
                    conn.commit()
                    print(f"Accident recorded at {timestamp}")
                    accident_detected = True
                    cooldown_counter = cooldown_frames

    # Cooldown logic
    if cooldown_counter > 0:
        cooldown_counter -= 1
    else:
        accident_detected = False

    cv2.imshow("Remote Webcam (Accident Detection)", frame)
    if cv2.waitKey(1) == ord('q'):
        break

client_socket.close()
cursor.close()
conn.close()
cv2.destroyAllWindows()
