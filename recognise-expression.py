import os
# Disable oneDNN optimizations that cause LLVM errors
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras

# Additional TensorFlow configuration to avoid half-precision issues
tf.config.set_soft_device_placement(True)

# Load the trained model
MODEL_PATH = 'models/final/emotion_recognition_ft_20251116_115814.keras'
try:
    model = keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit(1)

# Emotion labels (must match training)
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

# Load Face Cascade Classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def preprocess_face(face_img):
    """
    Preprocess the face image for the model:
    - Convert to grayscale (if not already)
    - Resize to 48x48
    - Normalize to [0, 1]
    - Reshape to (1, 48, 48, 1)
    """
    try:
        # Resize to model input size
        face_resized = cv2.resize(face_img, (48, 48))
        
        # Normalize
        face_normalized = face_resized / 255.0
        
        # Reshape: (1, 48, 48, 1)
        face_reshaped = np.reshape(face_normalized, (1, 48, 48, 1))
        return face_reshaped
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def main():
    # Initialize Webcam - simple version
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Starting webcam... Press 'q' to quit.")

    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

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
                # Predict
                predictions = model.predict(processed_face, verbose=0)
                
                # Get label
                max_index = np.argmax(predictions[0])
                emotion = EMOTION_LABELS[max_index]
                confidence = predictions[0][max_index]

                # Display label
                label_text = f"{emotion} ({confidence*100:.1f}%)"
                cv2.putText(frame, label_text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

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
