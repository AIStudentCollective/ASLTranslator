import os
import cv2
import mediapipe as mp
import numpy as np
import joblib
from flask import Flask, request, jsonify, render_template
import base64

app = Flask(__name__)

# --- Configuration (should match training) ---
NUM_FRAMES = 120
POSE_LANDMARKS = 33
HAND_LANDMARKS = 21
# (x,y) for each landmark
FEATURES_PER_FRAME = (POSE_LANDMARKS + 2 * HAND_LANDMARKS) * 2

# Inverse map for predictions (ensure this matches your training labels)
# This should correspond to the label_map used during training.

INV_LABEL_MAP = {
    0: "alright",
    1: "goodafternoon",
    2: "goodmorning",
    3: "hello",
    4: "howareyou",
}

# --- Load the trained pipeline ---
PIPELINE_PATH = "asl_pipeline_mediapipe3.joblib"  
if not os.path.exists(PIPELINE_PATH):
    raise FileNotFoundError(
        f"Pipeline file not found at {PIPELINE_PATH}. "
        "Please ensure the path is correct."
    )
pipeline = joblib.load(PIPELINE_PATH)

# --- MediaPipe Holistic Initialization  ---
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,  # Process video stream
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def base64_to_image(base64_string):
    """Convert base64 string to OpenCV image."""
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    img_bytes = base64.b64decode(base64_string)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img


def extract_keypoints_from_frame(frame):
    """
    Runs Holistic on one BGR frame and returns a (FEATURES_PER_FRAME,) array.
    Missing landmarks left as nan. Identical to training's extract_keypoints.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False  # To improve performance
    res = holistic.process(rgb)
    rgb.flags.writeable = True

    # Initialize with NaNs (as in training)
    px = np.full(POSE_LANDMARKS, np.nan, dtype=np.float32)
    py = np.full(POSE_LANDMARKS, np.nan, dtype=np.float32)
    lhx = np.full(HAND_LANDMARKS, np.nan, dtype=np.float32)
    lhy = np.full(HAND_LANDMARKS, np.nan, dtype=np.float32)
    rhx = np.full(HAND_LANDMARKS, np.nan, dtype=np.float32)
    rhy = np.full(HAND_LANDMARKS, np.nan, dtype=np.float32)

    if res.pose_landmarks:
        for i, lm in enumerate(
            res.pose_landmarks.landmark[:POSE_LANDMARKS]
        ):
            px[i], py[i] = lm.x, lm.y
    if res.left_hand_landmarks:
        for i, lm in enumerate(
            res.left_hand_landmarks.landmark[:HAND_LANDMARKS]
        ):
            lhx[i], lhy[i] = lm.x, lm.y
    if res.right_hand_landmarks:
        for i, lm in enumerate(
            res.right_hand_landmarks.landmark[:HAND_LANDMARKS]
        ):
            rhx[i], rhy[i] = lm.x, lm.y

    return np.concatenate([px, py, lhx, lhy, rhx, rhy])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        frames_base64 = data.get("frames", [])

        if not frames_base64 or len(frames_base64) == 0:
            return jsonify({"error": "No frames received"}), 400

        all_frame_keypoints = []
        prev_kp = None

        for frame_b64 in frames_base64:
            img = base64_to_image(frame_b64)
            if img is None:
                # Skip corrupted frame, or handle as all NaNs
                # For simplicity, we'll create NaNs matching feature size
                kp = np.full(FEATURES_PER_FRAME, np.nan, dtype=np.float32)
            else:
                kp = extract_keypoints_from_frame(img)

            # Carry forward logic (from training)
            if np.isnan(kp).any() and prev_kp is not None:
                kp = prev_kp
            kp_filled = np.nan_to_num(
                kp, nan=0.0
            )  # Fill remaining NaNs with 0
            all_frame_keypoints.append(kp_filled)
            prev_kp = kp_filled  # Update prev_kp with the filled version

        # Pad or truncate frames (from training)
        num_received_frames = len(all_frame_keypoints)
        if num_received_frames == 0: # Should be caught by earlier check, but defensive
             return jsonify({"error": "Could not process any frames"}), 400

        if num_received_frames < NUM_FRAMES:
            last_valid_frame_kp = all_frame_keypoints[-1]
            padding = [
                last_valid_frame_kp
                for _ in range(NUM_FRAMES - num_received_frames)
            ]
            all_frame_keypoints.extend(padding)
        elif num_received_frames > NUM_FRAMES:
            all_frame_keypoints = all_frame_keypoints[:NUM_FRAMES]

        # Flatten to a single feature vector (as in training)
        feature_vector = np.array(
            all_frame_keypoints, dtype=np.float32
        ).flatten()

        # Reshape for the pipeline (expects 2D array: [n_samples, n_features])
        feature_vector_reshaped = feature_vector.reshape(1, -1)

        if feature_vector_reshaped.shape[1] != (
            NUM_FRAMES * FEATURES_PER_FRAME
        ):
            return jsonify(
                {
                    "error": f"Feature vector shape mismatch. "
                    f"Expected {NUM_FRAMES * FEATURES_PER_FRAME}, "
                    f"got {feature_vector_reshaped.shape[1]}"
                }
            ), 500

        # Make prediction
        prediction_index = pipeline.predict(feature_vector_reshaped)[0]
        probabilities = pipeline.predict_proba(feature_vector_reshaped)[0]

        predicted_label_str = INV_LABEL_MAP.get(
            int(prediction_index), "Unknown Label"
        )
        confidence = float(probabilities[pipeline.classes_ == prediction_index][0])


        return jsonify(
            {
                "prediction": predicted_label_str,
                "confidence": round(confidence, 4),
                "debug_num_frames_processed": len(all_frame_keypoints),
                "debug_feature_vector_shape": feature_vector_reshaped.shape
            }
        )

    except Exception as e:
        app.logger.error(f"Error during prediction: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # When deploying, use a production WSGI server like Gunicorn or Waitress
    app.run(host="0.0.0.0", port=8000, debug=True) # Debug=False for production
