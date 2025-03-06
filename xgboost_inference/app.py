from flask import Flask
from flask_socketio import SocketIO, emit
import numpy as np
import json
import joblib
import base64
import cv2
import mediapipe as mp
import os
from sklearn.base import BaseEstimator, TransformerMixin
import xgboost as xgb

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60)

# Constants
NUM_FRAMES = 120
FEATURES_PER_FRAME = 134  # 25 pose_x + 25 pose_y + 21 hand1_x + 21 hand1_y + 21 hand2_x + 21 hand2_y

print("Starting application...")

# Initialize MediaPipe Pose and Hands
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Optional center crop function for preprocessing frames
def center_crop(frame, crop_fraction=0.4):
    """
    Crops the center of the frame to a specified fraction of its original size.
    
    Args:
        frame: Input frame as a numpy array (height, width, channels).
        crop_fraction: Fraction of original size to crop to (default 0.4).
    
    Returns:
        Cropped frame.
    """
    h, w, _ = frame.shape
    new_w = int(w * crop_fraction)
    new_h = int(h * crop_fraction)
    start_x = (w - new_w) // 2
    start_y = (h - new_h) // 2
    return frame[start_y:start_y+new_h, start_x:start_x+new_w]

# Keypoint extraction function
def extract_keypoints(frame):
    """
    Extracts keypoints from a frame using MediaPipe Pose and Hands.
    
    Args:
        frame: Input frame as a numpy array.
    
    Returns:
        Dictionary containing pose and hand keypoints (x, y coordinates).
    """
    # Optionally apply center crop (uncomment to enable)
    # frame = center_crop(frame)

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose_results = pose.process(image)
    hand_results = hands.process(image)

    keypoints = {
        'pose_x': [], 'pose_y': [],
        'hand1_x': [], 'hand1_y': [],
        'hand2_x': [], 'hand2_y': []
    }

    # Extract pose landmarks (first 25)
    if pose_results.pose_landmarks:
        for i, landmark in enumerate(pose_results.pose_landmarks.landmark[:25]):
            keypoints['pose_x'].append(landmark.x)
            keypoints['pose_y'].append(landmark.y)
    else:
        keypoints['pose_x'] = [np.nan] * 25
        keypoints['pose_y'] = [np.nan] * 25

    # Extract hand landmarks
    if hand_results.multi_hand_landmarks:
        if len(hand_results.multi_hand_landmarks) > 0:
            for landmark in hand_results.multi_hand_landmarks[0].landmark:
                keypoints['hand1_x'].append(landmark.x)
                keypoints['hand1_y'].append(landmark.y)
        if len(hand_results.multi_hand_landmarks) > 1:
            for landmark in hand_results.multi_hand_landmarks[1].landmark:
                keypoints['hand2_x'].append(landmark.x)
                keypoints['hand2_y'].append(landmark.y)

    # Pad missing hand landmarks with np.nan
    if not keypoints['hand1_x']:
        keypoints['hand1_x'] = [np.nan] * 21
        keypoints['hand1_y'] = [np.nan] * 21
    if not keypoints['hand2_x']:
        keypoints['hand2_x'] = [np.nan] * 21
        keypoints['hand2_y'] = [np.nan] * 21

    return keypoints

# Process frames and predict gesture
def process_frames(frames):
    """
    Processes a list of frames to extract keypoints and predict a gesture.
    
    Args:
        frames: List of frames as numpy arrays.
    
    Returns:
        Prediction from the pipeline (integer label).
    """
    print(f"Processing {len(frames)} frames")

    keypoints = {
        'pose_x': [], 'pose_y': [],
        'hand1_x': [], 'hand1_y': [],
        'hand2_x': [], 'hand2_y': []
    }

    for i, frame in enumerate(frames):
        print(f"Processing frame {i+1}/{len(frames)}")
        frame_keypoints = extract_keypoints(frame)
        keypoints['pose_x'].append(frame_keypoints['pose_x'])
        keypoints['pose_y'].append(frame_keypoints['pose_y'])
        keypoints['hand1_x'].append(frame_keypoints['hand1_x'])
        keypoints['hand1_y'].append(frame_keypoints['hand1_y'])
        keypoints['hand2_x'].append(frame_keypoints['hand2_x'])
        keypoints['hand2_y'].append(frame_keypoints['hand2_y'])

    # Pad or truncate to NUM_FRAMES
    for key in keypoints:
        current_len = len(keypoints[key])
        if current_len < NUM_FRAMES:
            print(f"Padding {key} from {current_len} to {NUM_FRAMES} frames")
            keypoints[key].extend([[np.nan] * len(keypoints[key][0]) for _ in range(NUM_FRAMES - current_len)])
        elif current_len > NUM_FRAMES:
            print(f"Truncating {key} from {current_len} to {NUM_FRAMES} frames")
            keypoints[key] = keypoints[key][:NUM_FRAMES]

    # Save keypoints to a temporary JSON file
    temp_json_path = 'temp_keypoints.json'
    with open(temp_json_path, 'w') as f:
        json.dump(keypoints, f)

    print(f"Saved keypoints to {temp_json_path}")

    # Use the pipeline to predict
    print("Running prediction with pipeline...")
    prediction = pipeline.predict([temp_json_path])
    print(f"Raw prediction: {prediction}")

    # Clean up the temporary file
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)
        print(f"Removed temporary file {temp_json_path}")

    return prediction[0]

# Keypoint feature extraction classes and functions
def load_keypoints(json_path):
    """
    Loads keypoints from a JSON file.
    
    Args:
        json_path: Path to the JSON file.
    
    Returns:
        Dictionary of keypoints.
    """
    with open(json_path, "r") as f:
        data = json.load(f)
    return data

def create_feature_vector(data, num_frames=NUM_FRAMES):
    """
    Creates a flattened feature vector from keypoints.
    
    Args:
        data: Dictionary of keypoints.
        num_frames: Number of frames to process (default NUM_FRAMES).
    
    Returns:
        Flattened numpy array of features.
    """
    pose_x = data.get("pose_x", [])
    pose_y = data.get("pose_y", [])
    hand1_x = data.get("hand1_x", [])
    hand1_y = data.get("hand1_y", [])
    hand2_x = data.get("hand2_x", [])
    hand2_y = data.get("hand2_y", [])

    total_frames = len(pose_x)
    features = []

    for i in range(num_frames):
        if i < total_frames:
            frame_features = (
                pose_x[i] + pose_y[i] +
                hand1_x[i] + hand1_y[i] +
                hand2_x[i] + hand2_y[i]
            )
            # Ensure exactly FEATURES_PER_FRAME features
            if len(frame_features) > FEATURES_PER_FRAME:
                frame_features = frame_features[:FEATURES_PER_FRAME]
            elif len(frame_features) < FEATURES_PER_FRAME:
                frame_features += [np.nan] * (FEATURES_PER_FRAME - len(frame_features))
        else:
            frame_features = [np.nan] * FEATURES_PER_FRAME
        features.append(frame_features)

    return np.array(features).flatten()

class KeypointFeatureExtractor(BaseEstimator, TransformerMixin):
    """Custom transformer to extract features from keypoints."""
    def __init__(self, num_frames=NUM_FRAMES):
        self.num_frames = num_frames

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        all_features = []
        for path in X:
            data = load_keypoints(path)
            feat_vector = create_feature_vector(data, self.num_frames)
            all_features.append(feat_vector)
        return np.array(all_features)

# Load the trained pipeline
print("Loading pipeline...")
try:
    pipeline = joblib.load('asl_pipeline.joblib')
    print("Pipeline loaded successfully")
    print(f"Pipeline steps: {[name for name, _ in pipeline.steps]}")
except Exception as e:
    print(f"Error loading pipeline: {str(e)}")
    import traceback
    traceback.print_exc()
    raise

# Flask routes and Socket.IO handlers
@app.route('/')
def index():
    """Serves the index.html file."""
    return open('index.html').read()

@socketio.on('connect')
def handle_connect():
    """Handles client connection."""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnection."""
    print('Client disconnected')

@socketio.on('video_frames')
def handle_video_frames(data):
    """Processes video frames received from the client and emits a prediction."""
    print(f"Received video_frames event with {len(data.get('frames', []))} frames")

    try:
        frames = []
        for i, frame_data in enumerate(data['frames']):
            try:
                if ',' in frame_data:
                    frame_data = frame_data.split(',')[1]
                frame_bytes = base64.b64decode(frame_data)
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    print(f"Failed to decode frame {i}")
                    continue
                print(f"Frame {i} decoded, shape: {frame.shape}")
                frames.append(frame)
            except Exception as e:
                print(f"Error processing frame {i}: {str(e)}")

        print(f"Successfully processed {len(frames)} frames")

        if not frames:
            print("No valid frames received")
            emit('prediction', {'result': 'No valid frames received', 'error': True})
            return

        prediction = process_frames(frames)
        print(f"Model prediction: {prediction}")

        # Map prediction to gesture
        gesture_map = {0: 'hello', 1: 'good morning', 2: 'how are you'}
        result = gesture_map.get(int(prediction), 'unknown')

        emit('prediction', {'result': result})
        print(f"Emitted prediction: {result}")

    except Exception as e:
        print(f"Error in handle_video_frames: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('prediction', {'result': f'Error: {str(e)}', 'error': True})

# Run the server
if __name__ == '__main__':
    print("Starting server...")
    try:
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
    finally:
        print("Closing MediaPipe...")
        pose.close()
        hands.close()