import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import pathlib
import base64

# Try to import models
KERAS_MODEL = None
ONNX_SESSION = None
DEEPFACE_AVAILABLE = False

try:
    import tf_keras as keras
    MODEL_PATH = 'models/final/emotion_recognition_ft_20251116_115814.keras'
    if os.path.exists(MODEL_PATH):
        print(f"Loading Keras model from {MODEL_PATH}...")
        KERAS_MODEL = keras.models.load_model(MODEL_PATH)
        print(f"Keras model loaded successfully!")
except Exception as e:
    print(f"Could not load Keras model: {e}")

try:
    import onnxruntime as ort
    ONNX_PATH = 'emotion_model.onnx'
    if os.path.exists(ONNX_PATH):
        print(f"Loading ONNX model from {ONNX_PATH}...")
        ONNX_SESSION = ort.InferenceSession(ONNX_PATH)
        print(f"ONNX model loaded successfully!")
except Exception as e:
    print(f"Could not load ONNX model: {e}")

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("DeepFace is available!")
except ImportError:
    print("DeepFace not available")

from PIL import Image
import io

app = Flask(__name__, static_folder='static')
CORS(app)

# Emotion labels (7 classes based on the model)
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

# Global settings
current_camera_index = 0
current_model_type = 'deepface'  # 'deepface', 'onnx', or 'keras'

def enumerate_cameras(max_cameras=10):
    """Find all available cameras and test them"""
    available_cameras = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                # Check if frame is not black
                if np.mean(frame) > 10:  # Simple brightness check
                    available_cameras.append({
                        'index': i,
                        'name': f'Camera {i}',
                        'working': True
                    })
                else:
                    available_cameras.append({
                        'index': i,
                        'name': f'Camera {i}',
                        'working': False
                    })
            cap.release()
    
    return available_cameras

def preprocess_face_for_onnx(face_img):
    """Prepare face for ONNX model"""
    try:
        face_resized = cv2.resize(face_img, (48, 48))
        face_normalized = face_resized.astype(np.float32) / 255.0
        return np.reshape(face_normalized, (1, 48, 48, 1))
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def preprocess_face_for_keras(face_img):
    """Prepare face for Keras model"""
    try:
        img_pil = Image.fromarray(face_img)
        img_pil = img_pil.resize((48, 48))
        img_array = np.array(img_pil)
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        img_array = np.expand_dims(img_array, axis=-1)
        return img_array
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def draw_rounded_rectangle(img, pt1, pt2, color, thickness, radius):
    """Draw a rectangle with rounded corners"""
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Draw straight lines
    cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
    cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
    cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
    cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
    
    # Draw corners
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

def process_frame_with_onnx(frame, face_cascade):
    """Process frame using ONNX model"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    results = []
    for (x, y, w, h) in faces:
        face_roi = gray_frame[y:y + h, x:x + w]
        processed_face = preprocess_face_for_onnx(face_roi)
        
        if processed_face is not None:
            try:
                input_name = ONNX_SESSION.get_inputs()[0].name
                predictions = ONNX_SESSION.run(None, {input_name: processed_face})[0]
                max_index = np.argmax(predictions[0])
                emotion = EMOTION_LABELS[max_index]
                confidence = float(predictions[0][max_index])
                
                # Draw cyan rounded rectangle
                cyan_color = (255, 255, 0)  # BGR: Cyan
                draw_rounded_rectangle(frame, (x, y), (x + w, y + h), cyan_color, 2, 15)
                
                # Draw label with emotion and confidence
                label_text = f"{emotion} {int(confidence * 100)}%"
                
                # Get text size for background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
                
                # Draw semi-transparent background for text
                overlay = frame.copy()
                cv2.rectangle(overlay, (x, y - text_height - 10), (x + text_width + 10, y), cyan_color, -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                # Draw text
                cv2.putText(frame, label_text, (x + 5, y - 5), font, font_scale, cyan_color, thickness)
                
                results.append({
                    'box': [int(x), int(y), int(w), int(h)],
                    'emotion': emotion,
                    'confidence': confidence
                })
            except Exception as e:
                print(f"ONNX prediction error: {e}")
    
    return frame, results

def process_frame_with_keras(frame, face_cascade):
    """Process frame using Keras model"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    results = []
    for (x, y, w, h) in faces:
        face_roi = gray_frame[y:y + h, x:x + w]
        processed_face = preprocess_face_for_keras(face_roi)
        
        if processed_face is not None:
            try:
                predictions = KERAS_MODEL.predict(processed_face, verbose=0)
                max_index = np.argmax(predictions[0])
                emotion = EMOTION_LABELS[max_index]
                confidence = float(predictions[0][max_index])
                
                # Draw cyan rounded rectangle
                cyan_color = (255, 255, 0)  # BGR: Cyan
                draw_rounded_rectangle(frame, (x, y), (x + w, y + h), cyan_color, 2, 15)
                
                # Draw label with emotion and confidence
                label_text = f"{emotion} {int(confidence * 100)}%"
                
                # Get text size for background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
                
                # Draw semi-transparent background for text
                overlay = frame.copy()
                cv2.rectangle(overlay, (x, y - text_height - 10), (x + text_width + 10, y), cyan_color, -1)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                # Draw text
                cv2.putText(frame, label_text, (x + 5, y - 5), font, font_scale, cyan_color, thickness)
                
                results.append({
                    'box': [int(x), int(y), int(w), int(h)],
                    'emotion': emotion,
                    'confidence': confidence
                })
            except Exception as e:
                print(f"Keras prediction error: {e}")
    
    return frame, results

def process_frame_with_deepface(frame):
    """Process frame using DeepFace"""
    results = []
    try:
        # Use SSD backend which is more robust than OpenCV (Haar cascades)
        # enforce_detection=False allows it to return results even if confidence is low, 
        # but we need to filter out "whole image" detections if they occur.
        print("Analyzing frame with DeepFace (backend=ssd)...")
        analysis_results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='ssd', silent=True)
        
        for result in analysis_results:
            region = result['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            # Check if detection is basically the whole image (fallback behavior)
            frame_h, frame_w = frame.shape[:2]
            
            if w > frame_w * 0.9 and h > frame_h * 0.9:
                print("Ignoring whole-image detection (likely false positive)")
                continue
                
            emotion = result['dominant_emotion']
            emotion_score = result['emotion'][emotion]
            
            print(f"Face detected at {x},{y} {w}x{h} - Emotion: {emotion} ({emotion_score}%)")
            
            # Capitalize emotion
            emotion = emotion.capitalize()
            
            # Draw cyan rounded rectangle (on the processed frame, though frontend draws its own)
            cyan_color = (255, 255, 0)  # BGR: Cyan
            draw_rounded_rectangle(frame, (x, y), (x + w, y + h), cyan_color, 2, 15)
            
            # Draw label with emotion and confidence
            label_text = f"{emotion} {int(emotion_score)}%"
            
            # Get text size for background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
            
            # Draw semi-transparent background for text
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y - text_height - 10), (x + text_width + 10, y), cyan_color, -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
            
            # Draw text
            cv2.putText(frame, label_text, (x + 5, y - 5), font, font_scale, cyan_color, thickness)
            
            results.append({
                'box': [int(x), int(y), int(w), int(h)],
                'emotion': emotion,
                'confidence': emotion_score / 100.0
            })
            
    except Exception as e:
        print(f"DeepFace error: {e}")
    
    return frame, results

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'keras_available': KERAS_MODEL is not None,
        'onnx_available': ONNX_SESSION is not None,
        'deepface_available': DEEPFACE_AVAILABLE
    })

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get list of available cameras"""
    cameras = enumerate_cameras()
    
    # Find first working camera
    working_camera = next((cam for cam in cameras if cam['working']), None)
    
    return jsonify({
        'cameras': cameras,
        'current': current_camera_index,
        'recommended': working_camera['index'] if working_camera else 0
    })

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    models = []
    
    if DEEPFACE_AVAILABLE:
        models.append({'id': 'deepface', 'name': 'DeepFace', 'available': True})
    else:
        models.append({'id': 'deepface', 'name': 'DeepFace', 'available': False})
    
    if ONNX_SESSION is not None:
        models.append({'id': 'onnx', 'name': 'ONNX Model', 'available': True})
    else:
        models.append({'id': 'onnx', 'name': 'ONNX Model', 'available': False})
    
    if KERAS_MODEL is not None:
        models.append({'id': 'keras', 'name': 'Keras Model', 'available': True})
    else:
        models.append({'id': 'keras', 'name': 'Keras Model', 'available': False})
    
    return jsonify({
        'models': models,
        'current': current_model_type
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update camera and model settings"""
    global current_camera_index, current_model_type
    
    data = request.json
    
    if 'camera_index' in data:
        current_camera_index = int(data['camera_index'])
    
    if 'model_type' in data:
        model_type = data['model_type']
        if model_type == 'deepface' and DEEPFACE_AVAILABLE:
            current_model_type = 'deepface'
        elif model_type == 'onnx' and ONNX_SESSION is not None:
            current_model_type = 'onnx'
        elif model_type == 'keras' and KERAS_MODEL is not None:
            current_model_type = 'keras'
        else:
            return jsonify({'error': 'Model not available'}), 400
    
    return jsonify({
        'camera_index': current_camera_index,
        'model_type': current_model_type
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Predict emotion from uploaded image"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Convert to numpy array for OpenCV
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # Process based on selected model
        if current_model_type == 'deepface' and DEEPFACE_AVAILABLE:
            processed_frame, results = process_frame_with_deepface(img_cv)
        elif current_model_type == 'onnx' and ONNX_SESSION is not None:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            processed_frame, results = process_frame_with_onnx(img_cv, face_cascade)
        elif current_model_type == 'keras' and KERAS_MODEL is not None:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            processed_frame, results = process_frame_with_keras(img_cv, face_cascade)
        else:
            return jsonify({'error': 'No model available'}), 500
        
        if results:
            top_result = results[0]
            
            # Format all results for frontend - convert numpy types to Python types
            all_predictions = []
            for r in results:
                all_predictions.append({
                    'emotion': str(r['emotion']),  # Ensure string
                    'confidence': float(r['confidence'])  # Convert numpy float32 to Python float
                })
            
            return jsonify({
                'success': True,
                'prediction': str(top_result['emotion']),
                'confidence': float(top_result['confidence']),  # Convert numpy float32 to Python float
                'box': [int(x) for x in top_result['box']],  # Ensure all box values are Python ints
                'all_predictions': all_predictions
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No face detected'
            }), 400
    
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Auto-detect working camera
    print("Detecting cameras...")
    cameras = enumerate_cameras()
    working_camera = next((cam for cam in cameras if cam['working']), None)
    
    if working_camera:
        current_camera_index = working_camera['index']
        print(f"Default camera set to index {current_camera_index}")
    else:
        print("No working camera detected, using index 0")
    
    # Set default model
    if DEEPFACE_AVAILABLE:
        current_model_type = 'deepface'
        print("Default model: DeepFace")
    elif ONNX_SESSION is not None:
        current_model_type = 'onnx'
        print("Default model: ONNX")
    elif KERAS_MODEL is not None:
        current_model_type = 'keras'
        print("Default model: Keras")
    else:
        print("WARNING: No models available!")
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
    
