import numpy as np


def eye_aspect_ratio(eye):
    # eye is an array of 6 (x, y) points
    a = np.linalg.norm(eye[1] - eye[5])
    b = np.linalg.norm(eye[2] - eye[4])
    c = np.linalg.norm(eye[0] - eye[3])
    if c == 0:
        return 0.0
    return (a + b) / (2.0 * c)


def blink_detected(ear, threshold):
    return ear < threshold
