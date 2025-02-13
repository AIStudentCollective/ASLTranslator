############################
# gesture_recognizer.py
############################

import os
import csv
import copy

import cv2 as cv
import numpy as np
import mediapipe as mp

from model.keypoint_classifier.keypoint_classifier import KeyPointClassifier

# If you rely on a different location for your labels CSV, adjust the path here.
KEYPOINT_CLASSIFIER_LABEL_PATH = "model/keypoint_classifier/keypoint_classifier_label.csv"

# Initialize Mediapipe hands detection once to avoid re-initialization overhead
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,         # Static mode for single image
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

# Initialize KeyPointClassifier once
keypoint_classifier = KeyPointClassifier()

# Load labels
with open(KEYPOINT_CLASSIFIER_LABEL_PATH, encoding="utf-8-sig") as f:
    keypoint_classifier_labels = csv.reader(f)
    keypoint_classifier_labels = [row[0] for row in keypoint_classifier_labels]


def detect_hand_gesture(image: np.ndarray) -> str:
    """
    Process the given image (as a BGR numpy array) to detect hand gestures
    using Mediapipe and a pre-trained keypoint classifier.

    :param image: BGR image array (numpy.ndarray)
    :return: A string label of the detected gesture (or None if no hands found)
    """

    # Convert to RGB as Mediapipe expects RGB images
    rgb_image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

    # Process with Mediapipe
    results = hands.process(rgb_image)

    # If no hand landmarks are detected, return None
    if not results.multi_hand_landmarks:
        return None

    # For simplicity, let's only classify the first detected hand
    # You could extend this to handle multiple hands
    hand_landmarks = results.multi_hand_landmarks[0]

    # Calculate relative/normalized coordinates of the hand
    landmark_list = _calc_landmark_list(image, hand_landmarks)
    pre_processed_landmark_list = _pre_process_landmark(landmark_list)

    # Classify the hand gesture
    hand_sign_id = keypoint_classifier(pre_processed_landmark_list)
    hand_sign_text = keypoint_classifier_labels[hand_sign_id]

    return hand_sign_text


def _calc_landmark_list(image, landmarks):
    """
    Convert Mediapipe landmarks to pixel coordinates for the given image.
    """
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point


def _pre_process_landmark(landmark_list):
    """
    Normalizes landmark coordinates:
      1. Translates so that the first landmark (wrist) is the origin.
      2. Scales all coordinates by the max absolute value.
      3. Flattens into a one-dimensional list.
    """
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Translate so that the first point is the origin
    base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]
    for index, landmark_point in enumerate(temp_landmark_list):
        temp_landmark_list[index][0] -= base_x
        temp_landmark_list[index][1] -= base_y

    # Flatten
    temp_landmark_list = [coord for point in temp_landmark_list for coord in point]

    # Normalize
    max_value = max(list(map(abs, temp_landmark_list)))  # find the largest absolute val
    if max_value == 0:
        max_value = 1  # Avoid division by zero if the hand is a single point
    temp_landmark_list = [n / max_value for n in temp_landmark_list]

    return temp_landmark_list