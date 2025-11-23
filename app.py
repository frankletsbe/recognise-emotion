import os
import numpy as np
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

def preprocess_image(image_file):
    """
    Preprocess the uploaded image for model prediction.
    - Convert to grayscale
    - Resize to 48x48
    - Normalize pixel values
    """
    # Read image
    img = Image.open(image_file)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Resize to 48x48
    img = img.resize((48, 48))
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Normalize pixel values to [0, 1]
    img_array = img_array / 255.0
    
    # Add batch and channel dimensions: (1, 48, 48, 1)
    img_array = np.expand_dims(img_array, axis=0)
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
    Predict emotion from uploaded image.
    Expects a file upload with key 'file'.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Preprocess the image
        img_array = preprocess_image(file)
        
        # Make prediction
        predictions = model.predict(img_array, verbose=0)
        
        # Get probabilities for all emotions
        probabilities = predictions[0].tolist()
        
        # Create response with all emotions and their confidence scores
        results = []
        for i, emotion in enumerate(EMOTION_LABELS):
            results.append({
                'emotion': emotion,
                'confidence': float(probabilities[i])
            })
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Get the top prediction
        top_emotion = results[0]['emotion']
        top_confidence = results[0]['confidence']
        
        return jsonify({
            'success': True,
            'prediction': top_emotion,
            'confidence': top_confidence,
            'all_predictions': results
        })
    
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
