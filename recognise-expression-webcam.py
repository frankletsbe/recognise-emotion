import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
# Enable legacy Keras API for DeepFace compatibility
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import cv2
import numpy as np
import argparse
import pathlib
import sys
import onnxruntime as ort
import tf_keras as keras

DEEPFACE_AVAILABLE = False

# Emotion labels (must match training for Keras model)
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

def preprocess_face(face_img):
    """
    Prepare a face ROI for the ONNX model:
    - Resize to 48×48
    - Scale to [0, 1]
    - Convert to float32 and reshape to (1, 48, 48, 1)
    """
    try:
        face_resized = cv2.resize(face_img, (48, 48))
        face_normalized = face_resized.astype(np.float32) / 255.0
        return np.reshape(face_normalized, (1, 48, 48, 1))
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def run_keras_backend(frame, face_cascade, ort_session):
    # Convert to grayscale for face detection
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # Process each face
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        face_roi = gray_frame[y:y + h, x:x + w]
        processed_face = preprocess_face(face_roi)
        if processed_face is not None:
            try:
                input_name = ort_session.get_inputs()[0].name
                predictions = ort_session.run(None, {input_name: processed_face})[0]
                max_index = np.argmax(predictions[0])
                emotion = EMOTION_LABELS[max_index]
                confidence = predictions[0][max_index]
                label_text = f"{emotion} ({confidence * 100:.1f}%)"
                cv2.putText(frame, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except Exception as e:
                error_text = f"Err: {type(e).__name__}"
                cv2.putText(frame, error_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return frame

def run_deepface_backend(frame):
    try:
        from deepface import DeepFace
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='opencv', silent=True)
        for result in results:
            region = result['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            emotion = result['dominant_emotion']
            emotion_score = result['emotion'][emotion]
            label_text = f"{emotion} ({emotion_score:.1f}%)"
            cv2.putText(frame, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    except Exception:
        pass
    return frame

def main():
    parser = argparse.ArgumentParser(description="Real‑time emotion recogniser")
    parser.add_argument(
        "--model",
        default="emotion_model.onnx",
        help="Path to the ONNX model file (only for keras backend)"
    )
    parser.add_argument(
        "--backend",
        choices=['keras', 'deepface'],
        default='keras',
        help="Backend to use for emotion recognition: 'keras' (default) or 'deepface'"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="VideoCapture device index (0 = built‑in webcam, 1 = external camera, …)"
    )
    args = parser.parse_args()

    ort_session = None
    face_cascade = None

    if args.backend == 'keras':
        model_path = pathlib.Path(__file__).parent / args.model
        if not model_path.exists():
            print(f"Model file not found: {model_path}")
            sys.exit(1)
        try:
            ort_session = ort.InferenceSession(str(model_path))
            print(f"ONNX model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    elif args.backend == 'deepface':
        try:
            from deepface import DeepFace
            global DEEPFACE_AVAILABLE
            DEEPFACE_AVAILABLE = True
            print("Using DeepFace backend...")
        except ImportError:
            print("Error: DeepFace is not installed. Please install it with 'pip install deepface'")
            sys.exit(1)

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Starting webcam with {args.backend} backend... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        if args.backend == 'keras':
            frame = run_keras_backend(frame, face_cascade, ort_session)
        else:
            frame = run_deepface_backend(frame)
        cv2.imshow('Emotion Recognition - Real Time', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()