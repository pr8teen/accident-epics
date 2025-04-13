from ultralytics import YOLO
import cv2 as cv
import cvzone
import numpy as np
import psycopg2
from datetime import datetime

# PostgreSQL se connect karna
conn = psycopg2.connect(
    dbname="AccidentDB", 
    user="postgres", 
    password="dadmom2004", 
    host="localhost", 
    port="5432"
)
cursor = conn.cursor()

# YOLOv8 model load karna
model = YOLO("/Users/pr9teen/epics 2/runs/detect/train/weights/best.pt")

# Video load karna
video_path = "/Users/pr9teen/epics 2/videos_accidents/V6.mp4"
vid = cv.VideoCapture(video_path)

# Video ke details lena
fps = int(vid.get(cv.CAP_PROP_FPS))
width = int(vid.get(cv.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT))

# Output video save karne ke liye Video Writer define karna
output_path = "/Users/pr9teen/epics 2/runs/detect/predict4.mp4"
fourcc = cv.VideoWriter_fourcc(*'mp4v')
out = cv.VideoWriter(output_path, fourcc, fps, (width, height))

# Dummy CCTV Data (Actual GPS data se replace karna padega)
cctv_id = 1
latitude, longitude = 28.7041, 77.1025  # Yahan actual camera coordinates dalna

# Accident Detection State Variables
accident_detected = False  # Ye flag track karega ki accident record ho chuka hai ya nahi
cooldown_frames = 1500  # Accident detect hone ke baad 30 frames ke liye ignore karna
cooldown_counter = 0  # Cooldown counter track karne ke liye

while True:
    ret, frame = vid.read()
    if not ret:
        break  # Agar video khatam ho gaya toh loop se bahar niklo

    results = model(frame, stream=True)

    accident_in_frame = False  # Har frame ke liye reset karna

    for r in results:
        boxes = r.boxes  # Bounding boxes le lo

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordinates integer me convert karo
            confidence = box.conf[0].item()

            if confidence > 0.3:
                accident_in_frame = True  # Is frame me accident detect ho gaya

                # Red Bounding Box draw karo (Thicker)
                cvzone.cornerRect(frame, (x1, y1, x2 - x1, y2 - y1), colorR=(0, 0, 255), l=3)

                # Confidence Score display karo
                cv.putText(frame, f'Accident {confidence:.2f}', (x1, y1 - 10),
                           cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # Agar accident detect ho gaya aur pehle record nahi hua hai
                if not accident_detected:
                    # Current Timestamp lo
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # PostgreSQL me data insert karo
                    insert_query = """
                    INSERT INTO Accident_Reports (timestamp, cctv_id, latitude, longitude, weather_condition, road_condition, light_condition, vehicle_involved, vehicle_types, casualties, severity, police_verified) 
                    VALUES (%s, %s, %s, %s, 'Unknown', 'Unknown', 'Unknown', 1, 'Unknown', 0, 'Minor', FALSE);
                    """
                    cursor.execute(insert_query, (timestamp, cctv_id, latitude, longitude))
                    conn.commit()

                    print(f"Accident Recorded at {timestamp} (Lat: {latitude}, Lon: {longitude})")

                    # Cooldown activate karo taaki duplicate entries na ho
                    accident_detected = True
                    cooldown_counter = cooldown_frames

    # Cooldown management
    if cooldown_counter > 0:
        cooldown_counter -= 1
    else:
        accident_detected = False  # Accident detection flag reset karna

    # Video Frame display karo
    cv.imshow("YOLOv8 Detection", frame)
    out.write(frame)  # Frame ko output video me save karo

    if cv.waitKey(1) & 0xFF == ord('q'):
        break  # Agar 'q' dabaya toh exit karna

# Resources release karo
vid.release()
out.release()
cv.destroyAllWindows()
cursor.close()
conn.close()
print(f"Processing complete! Video saved at: {output_path}")
