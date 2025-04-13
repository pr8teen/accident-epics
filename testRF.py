from inference_sdk import InferenceHTTPClient
import cv2

# Initialize the client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="CzlyJb76DUBCn5CZWFWg"
)

# Function to process each frame of the video
def process_video(video_path, model_id, frame_skip=5, resize_scale=0.5):
    """
    Process a video for accident detection.
    
    Args:
        video_path (str): Path to the video file.
        model_id (str): Model ID for inference.
        frame_skip (int): Number of frames to skip between inferences.
        resize_scale (float): Scale factor to resize frames for faster processing.
    """
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    frame_count = 0
    
    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        
        if not ret:
            break  # Exit the loop if no more frames are available
        
        frame_count += 1
        
        # Skip frames to speed up processing
        if frame_count % frame_skip != 0:
            continue
        
        # Resize the frame for faster inference
        if resize_scale != 1.0:
            frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        
        # Perform inference on the frame
        result = CLIENT.infer(frame, model_id=model_id)
        
        # Check if an accident is detected
        if result['predictions']:  # Assuming the result contains a 'predictions' key
            for prediction in result['predictions']:
                if prediction['class'] == 'accident':  # Assuming 'accident' is the class name
                    print("Accident detected!")
                    # Draw bounding box on the frame
                    x, y, width, height = int(prediction['x']), int(prediction['y']), int(prediction['width']), int(prediction['height'])
                    cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
        
        # Display the frame (optional)
        cv2.imshow('Frame', frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the video capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

# Path to the video file
video_path = '/Users/pr9teen/epics 2/videos_accidents/V6.mp4'

# Model ID for accident detection
model_id = "accident-detection-model/2"

# Process the video with optimizations
process_video(video_path, model_id, frame_skip=5, resize_scale=0.5)