import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import numpy as np
import argparse
import pathlib
import sys
import onnxruntime as ort

DEEPFACE_AVAILABLE = False

# Emotion labels (must match training for Keras model)
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

def preprocess_face(face_img):
    """
    Preprocess the face image for the ONNX model:
    - Resize to 48x48
    - Normalize to [0, 1]
    - Reshape to (1, 48, 48, 1)
    """
    try:
        # Resize to model input size
        face_resized = cv2.resize(face_img, (48, 48))
        
        # Normalize
        face_normalized = face_resized / 255.0
        
        # Reshape: (1, 48, 48, 1) and convert to float32
        face_reshaped = np.reshape(face_normalized, (1, 48, 48, 1)).astype(np.float32)
        return face_reshaped
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
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Extract face ROI (Region of Interest)
        face_roi = gray_frame[y:y+h, x:x+w]

        # Preprocess
        processed_face = preprocess_face(face_roi)

        if processed_face is not None:
            try:
                # ONNX Runtime inference
                input_name = ort_session.get_inputs()[0].name
                predictions = ort_session.run(None, {input_name: processed_face})[0]
                
                # Get label
                max_index = np.argmax(predictions[0])
                emotion = EMOTION_LABELS[max_index]
                confidence = predictions[0][max_index]

                # Display label
                label_text = f"{emotion} ({confidence*100:.1f}%)"
                cv2.putText(frame, label_text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except Exception as e:
                # If prediction fails, display error on frame
                error_text = f"Err: {type(e).__name__}"
                cv2.putText(frame, error_text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return frame

def run_deepface_backend(frame):
    try:
        from deepface import DeepFace
        # DeepFace expects BGR (OpenCV default) or RGB. It handles conversion internally if needed.
        # enforce_detection=False allows it to return no face if none found, preventing crash
        # detector_backend='opencv' is faster for real-time
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='opencv', silent=True)
        
        # results is a list of dicts
        for result in results:
            # DeepFace returns 'region' with x, y, w, h
            region = result['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Get dominant emotion
            emotion = result['dominant_emotion']
            # Confidence is not always directly available in the same way as Keras, 
            # but 'emotion' key has probabilities.
            emotion_score = result['emotion'][emotion]
            
            # Display label
            label_text = f"{emotion} ({emotion_score:.1f}%)"
            cv2.putText(frame, label_text, (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
    except Exception as e:
        # DeepFace might raise errors if no face found and enforce_detection=True, 
        # but with False it should be safer. Still good to catch.
        pass
    return frame

def main():
    parser = argparse.ArgumentParser(description="Real‑time emotion recogniser")
    parser.add_argument(
        "--model",
        default="emotion_model.onnx",
        help="Path to the ONNX model file (only for keras backend)",
    )
    parser.add_argument(
        "--backend",
        choices=['keras', 'deepface'],
        default='keras',
        help="Backend to use for emotion recognition: 'keras' (default) or 'deepface'",
    )
    args = parser.parse_args()

    # Setup for Keras backend
    ort_session = None
    face_cascade = None
    
    if args.backend == 'keras':
        # Dynamically load the requested model
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
            
        # Load Face Cascade Classifier
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

    # Initialize Webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print(f"Starting webcam with {args.backend} backend... Press 'q' to quit.")

    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        if args.backend == 'keras':
            frame = run_keras_backend(frame, face_cascade, ort_session)
        else:
            frame = run_deepface_backend(frame)

        # Display the resulting frame
        cv2.imshow('Emotion Recognition - Real Time', frame)

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()