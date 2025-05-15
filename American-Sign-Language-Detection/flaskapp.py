from flask import Flask
from flask_socketio import SocketIO
import cv2
import numpy as np
import base64
import csv
import time
import mediapipe as mp
from model.keypoint_classifier.keypoint_classifier import KeyPointClassifier
from threading import Lock

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize model and mediapipe
keypoint_classifier = KeyPointClassifier()
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# Load labels
with open("model/keypoint_classifier/keypoint_classifier_label.csv", encoding="utf-8-sig") as f:
    keypoint_classifier_labels = [row[0] for row in csv.reader(f)]

process_lock = Lock()
frame_counter = 0

def calc_landmark_list(image, landmarks):
    """Convert landmarks to normalized coordinates."""
    return [(landmark.x, landmark.y) for landmark in landmarks.landmark]

def pre_process_landmark(landmark_list):
    """Normalize and process landmarks for model input."""
    if len(landmark_list) != 21:
        raise ValueError(f"Expected 21 landmarks, got {len(landmark_list)}")
    
    # Convert tuples to list format
    landmark_list = [[x, y] for x, y in landmark_list]
    
    # Get base point
    base_x, base_y = landmark_list[0][0], landmark_list[0][1]
    
    # Translate coordinates
    for i in range(len(landmark_list)):
        landmark_list[i][0] -= base_x
        landmark_list[i][1] -= base_y
    
    # Flatten and convert to numpy array
    flattened = np.array([coord for point in landmark_list for coord in point], dtype=np.float32)
    
    # Normalize
    max_value = max(abs(flattened.max()), abs(flattened.min()))
    if max_value != 0:
        flattened = flattened / max_value
        
    return flattened

@socketio.on('frame')
def handle_frame(data):
    global frame_counter
    
    with process_lock:
        try:
            current_timestamp = frame_counter * 1000
            frame_counter += 1

            # Decode image
            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # Mirror and convert for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            rgb_image = cv2.flip(rgb_image, 1)
            rgb_image.flags.writeable = False
            
            results = hands.process(rgb_image)
            rgb_image.flags.writeable = True
            
            gesture = 'No hand detected'
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    try:
                        raw_landmarks = calc_landmark_list(rgb_image, hand_landmarks)
                        processed_landmarks = pre_process_landmark(raw_landmarks)
                        hand_sign_id = keypoint_classifier(processed_landmarks)
                        gesture = keypoint_classifier_labels[hand_sign_id]
                    except Exception as e:
                        socketio.emit('prediction', {
                            'error': str(e),
                            'timestamp': current_timestamp
                        })
                        continue
                    break

            socketio.emit('prediction', {
                'gesture': gesture,
                'timestamp': current_timestamp
            })

        except Exception as e:
            socketio.emit('prediction', {
                'error': str(e),
                'timestamp': current_timestamp
            })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)