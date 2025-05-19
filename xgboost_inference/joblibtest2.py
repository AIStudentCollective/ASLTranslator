from joblib import load
import cv2, numpy as np
# Constants must match your training code:
NUM_FRAMES        = 120
POSE_LANDMARKS    = 33
HAND_LANDMARKS    = 21
FEATURES_PER_FRAME = (POSE_LANDMARKS + 2*HAND_LANDMARKS) * 2
# Load your fitted pipeline
model = load("asl_pipeline_mediapipe2.joblib")
# Invert your LABEL_MAP so you can print class names
LABEL_MAP = {
    'alright':       0,
    'goodafternoon': 1,
    'goodmorning':   2,
    'hello':         3,
    'howareyou':     4
}
inv_label_map = {v:k for k,v in LABEL_MAP.items()}
# Reuse your extract_keypoints(frame) function here…
def video_to_feature_vector(video_path):
    cap = cv2.VideoCapture(video_path)
    feats = []
    prev_kp = None
    for _ in range(NUM_FRAMES):
        ret, frame = cap.read()
        if not ret:
            break
        kp = extract_keypoints(frame)  # returns (FEATURES_PER_FRAME,) array
        # carry forward missing
        if np.isnan(kp).any() and prev_kp is not None:
            kp = prev_kp
        kp = np.nan_to_num(kp, nan=0.0)
        feats.append(kp)
        prev_kp = kp
    cap.release()
    # pad or truncate
    if len(feats) == 0:
        feats = [np.zeros(FEATURES_PER_FRAME, dtype=np.float32)] * NUM_FRAMES
    elif len(feats) < NUM_FRAMES:
        feats += [feats[-1]] * (NUM_FRAMES - len(feats))
    else:
        feats = feats[:NUM_FRAMES]
    fv = np.stack(feats, axis=0).astype(np.float32)  # (NUM_FRAMES, FPF)
    return fv.flatten().reshape(1, -1)               # (1, NUM_FRAMES*FPF)
# Now run it:
fv = video_to_feature_vector("/content/drive/MyDrive/AISC/Greeting_Augmented/Hello/MVI_0031_orig.mp4")
pred_id   = model.predict(fv)[0]
pred_probs= model.predict_proba(fv)[0]
print("Predicted class:", inv_label_map[pred_id])
print("Class probabilities:")
for cls_id, prob in enumerate(pred_probs):
    print(f"  {inv_label_map[cls_id]:<14s} {prob:.3f}")