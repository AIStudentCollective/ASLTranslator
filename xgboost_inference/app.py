from flask import Flask, request, jsonify, render_template
import numpy as np
import mediapipe as mp
import cv2
import base64
import joblib
from sklearn.base import BaseEstimator, TransformerMixin
import re

app = Flask(__name__)

# Constants
NUM_FRAMES = 120
FEATURES_PER_FRAME = 134  # 33*2 (pose) + 21*2 (hand1) + 21*2 (hand2)

# Feature extractor class needed for the pipeline
class KeypointFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, num_frames=NUM_FRAMES):
        self.num_frames = num_frames
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        # During inference, we'll create feature vectors differently
        # This is just for pipeline compatibility
        return np.array(X)

# Load the pre-trained pipeline
pipeline = joblib.load('asl_pipeline.joblib')

# Initialize MediaPipe
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

def base64_to_image(base64_string):
    """Convert base64 string to numpy array image."""
    # Remove the "data:image/jpeg;base64," prefix if present
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    
    # Decode base64 string to bytes
    img_bytes = base64.b64decode(base64_string)
    
    # Convert bytes to numpy array
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    
    # Decode the numpy array as an image
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    return img

def process_frame(frame):
    """Extract landmarks from a single frame using MediaPipe."""
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame
    results = holistic.process(frame_rgb)
    
    # Initialize arrays for landmarks
    pose_x = np.zeros(33)  # 33 pose landmarks
    pose_y = np.zeros(33)
    hand1_x = np.zeros(21)  # 21 hand landmarks
    hand1_y = np.zeros(21)
    hand2_x = np.zeros(21)
    hand2_y = np.zeros(21)
    
    # Extract pose landmarks (only first 33 landmarks)
    if results.pose_landmarks:
        for idx, landmark in enumerate(results.pose_landmarks.landmark[:33]):
            pose_x[idx] = landmark.x
            pose_y[idx] = landmark.y
    
    # Extract hand landmarks (only first 21 landmarks per hand)
    if results.left_hand_landmarks:
        for idx, landmark in enumerate(results.left_hand_landmarks.landmark[:21]):
            hand1_x[idx] = landmark.x
            hand1_y[idx] = landmark.y
            
    if results.right_hand_landmarks:
        for idx, landmark in enumerate(results.right_hand_landmarks.landmark[:21]):
            hand2_x[idx] = landmark.x
            hand2_y[idx] = landmark.y
    
    # Convert numpy arrays to lists and ensure all values are float
    return {
        'pose_x': pose_x.astype(float).tolist(),
        'pose_y': pose_y.astype(float).tolist(),
        'hand1_x': hand1_x.astype(float).tolist(),
        'hand1_y': hand1_y.astype(float).tolist(),
        'hand2_x': hand2_x.astype(float).tolist(),
        'hand2_y': hand2_y.astype(float).tolist()
    }

def create_feature_vector(landmarks_data):
    """Create a feature vector from the landmarks data."""
    # Convert all landmark lists to numpy arrays first
    for key in landmarks_data:
        landmarks_data[key] = [np.array(frame, dtype=float) for frame in landmarks_data[key]]
    
    # Print initial frame count
    print(f"Initial frame count: {len(landmarks_data['pose_x'])}")
    
    # Ensure we have NUM_FRAMES frames
    num_frames = len(landmarks_data['pose_x'])
    if num_frames < NUM_FRAMES:
        # Pad with NaN if we have fewer frames
        pad_length = NUM_FRAMES - num_frames
        for key in landmarks_data:
            landmarks_data[key].extend([np.full_like(landmarks_data[key][0], np.nan)] * pad_length)
    elif num_frames > NUM_FRAMES:
        # Truncate if we have more frames
        for key in landmarks_data:
            landmarks_data[key] = landmarks_data[key][:NUM_FRAMES]
    
    print(f"After frame adjustment: {len(landmarks_data['pose_x'])} frames")
    
    # Flatten the features
    feature_vector = []
    for i in range(NUM_FRAMES):
        frame_features = []
        # Pose landmarks (33 points * 2 coordinates = 66 features)
        pose_x = landmarks_data['pose_x'][i][:33]  # Ensure 33 points
        pose_y = landmarks_data['pose_y'][i][:33]  # Ensure 33 points
        # Hand 1 landmarks (21 points * 2 coordinates = 42 features)
        hand1_x = landmarks_data['hand1_x'][i][:21]  # Ensure 21 points
        hand1_y = landmarks_data['hand1_y'][i][:21]  # Ensure 21 points
        # Hand 2 landmarks (21 points * 2 coordinates = 42 features)
        hand2_x = landmarks_data['hand2_x'][i][:21]  # Ensure 21 points
        hand2_y = landmarks_data['hand2_y'][i][:21]  # Ensure 21 points
        
        # Print dimensions for first frame
        if i == 0:
            print(f"Frame 0 feature dimensions:")
            print(f"- Pose X: {len(pose_x)}, Pose Y: {len(pose_y)}")
            print(f"- Hand1 X: {len(hand1_x)}, Hand1 Y: {len(hand1_y)}")
            print(f"- Hand2 X: {len(hand2_x)}, Hand2 Y: {len(hand2_y)}")
        
        frame_features.extend(pose_x)
        frame_features.extend(pose_y)
        frame_features.extend(hand1_x)
        frame_features.extend(hand1_y)
        frame_features.extend(hand2_x)
        frame_features.extend(hand2_y)
        
        if i == 0:
            print(f"Frame 0 total features: {len(frame_features)}")
        
        feature_vector.extend(frame_features)
    
    # Convert to numpy array, replace inf/-inf with nan, then replace nan with 0
    feature_vector = np.array(feature_vector, dtype=float)
    feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Verify feature vector size
    expected_size = NUM_FRAMES * FEATURES_PER_FRAME  # Should be 120 * 134 = 16080
    actual_size = len(feature_vector)
    if actual_size != expected_size:
        print(f"Warning: Feature vector size mismatch. Expected {expected_size}, got {actual_size}")
        print(f"Features per frame: {actual_size / NUM_FRAMES}")
        # Pad or truncate if necessary
        if actual_size < expected_size:
            feature_vector = np.pad(feature_vector, (0, expected_size - actual_size))
        else:
            feature_vector = feature_vector[:expected_size]
    
    return feature_vector.reshape(1, -1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get frames from request
        data = request.json
        frames = data.get('frames', [])
        
        if not frames:
            return jsonify({'error': 'No frames received'}), 400
        
        # Process each frame to extract landmarks
        all_landmarks = {
            'pose_x': [], 'pose_y': [],
            'hand1_x': [], 'hand1_y': [],
            'hand2_x': [], 'hand2_y': []
        }
        
        for frame_base64 in frames:
            # Convert base64 to image
            frame = base64_to_image(frame_base64)
            
            # Extract landmarks
            frame_landmarks = process_frame(frame)
            
            # Collect landmarks
            for key in all_landmarks:
                all_landmarks[key].append(frame_landmarks[key])
        
        # Create feature vector
        X = create_feature_vector(all_landmarks)
        
        # Make prediction
        prediction = pipeline.predict(X)[0]
        probabilities = pipeline.predict_proba(X)[0]
        confidence = float(probabilities[prediction])  # Convert numpy float to Python float
        
        # Map prediction index to label
        label_map = {
            0: 'alright',
            1: 'goodafternoon',
            2: 'goodmorning',
            3: 'hello',
            4: 'howareyou'
        }
        
        predicted_label = label_map[prediction]
        
        return jsonify({
            'prediction': predicted_label,
            'confidence': confidence
        })
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)