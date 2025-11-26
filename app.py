import os
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from tensorflow import keras
from PIL import Image
import io

app = Flask(__name__, static_folder='static')
CORS(app)

# Emotion labels (7 classes based on the model)
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

# Load the model at startup
MODEL_PATH = 'outputs/20251116_213701/emotion_recognition_ft_20251116_213701.keras'
print(f"Loading model from {MODEL_PATH}...")
model = keras.models.load_model(MODEL_PATH)
print(f"Model loaded successfully!")
print(f"Input shape: {model.input_shape}")
print(f"Output shape: {model.output_shape}")

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def preprocess_image(image_array):
    """
    Preprocess the face image for model prediction.
    - Convert to grayscale
    - Resize to 48x48
    - Normalize pixel values
    """
    # Convert to grayscale if needed
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_array
    
    # Resize to 48x48
    resized = cv2.resize(gray, (48, 48))
    
    # Normalize pixel values to [0, 1]
    normalized = resized / 255.0
    
    # Add batch and channel dimensions: (1, 48, 48, 1)
    img_array = np.expand_dims(normalized, axis=0)
    img_array = np.expand_dims(img_array, axis=-1)
    
    return img_array

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health():
    """Health check endpoint for Docker"""
    return jsonify({'status': 'healthy', 'model_loaded': model is not None})

@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict emotion from uploaded image with face detection.
    Expects a file upload with key 'file'.
    Returns bounding boxes and emotions for all detected faces.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read image file
        image_bytes = file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            return jsonify({
                'success': True,
                'faces_detected': 0,
                'message': 'No faces detected in the image'
            })
        
        # Process each detected face
        results = []
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Preprocess the face for emotion prediction
            img_array = preprocess_image(face_roi)
            
            # Make prediction
            predictions = model.predict(img_array, verbose=0)
            
            # Get probabilities for all emotions
            probabilities = predictions[0].tolist()
            
            # Create emotion results
            emotion_results = []
            for i, emotion in enumerate(EMOTION_LABELS):
                emotion_results.append({
                    'emotion': emotion,
                    'confidence': float(probabilities[i])
                })
            
            # Sort by confidence (highest first)
            emotion_results.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Get the top prediction
            top_emotion = emotion_results[0]['emotion']
            top_confidence = emotion_results[0]['confidence']
            
            # Add face result with bounding box
            results.append({
                'bounding_box': {
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                },
                'prediction': top_emotion,
                'confidence': top_confidence,
                'all_predictions': emotion_results
            })
        
        return jsonify({
            'success': True,
            'faces_detected': len(faces),
            'faces': results
        })
        
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)