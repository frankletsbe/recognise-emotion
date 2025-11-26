"""
Test suite for emotion recognition app.py

This module tests the Flask application endpoints, model loading,
camera detection, and emotion prediction functionality.
"""

import pytest
import json
import io
import os
import sys
from PIL import Image
import numpy as np

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as emotion_app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    emotion_app.app.config['TESTING'] = True
    with emotion_app.app.test_client() as client:
        yield client


@pytest.fixture
def sample_face_image():
    """Create a sample grayscale face image for testing"""
    # Create a 200x200 grayscale image with a simple face-like pattern
    img = Image.new('L', (200, 200), color=128)
    pixels = img.load()
    
    # Draw a simple face pattern (eyes and mouth)
    # Left eye
    for i in range(60, 80):
        for j in range(70, 90):
            pixels[i, j] = 0
    
    # Right eye
    for i in range(120, 140):
        for j in range(70, 90):
            pixels[i, j] = 0
    
    # Mouth (smile)
    for i in range(70, 130):
        j = int(140 + 20 * np.sin((i - 70) * np.pi / 60))
        if 0 <= j < 200:
            pixels[i, j] = 0
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


class TestHealthEndpoint:
    """Tests for the /health endpoint"""
    
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint is accessible"""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON"""
        response = client.get('/health')
        assert response.content_type == 'application/json'
    
    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns expected fields"""
        response = client.get('/health')
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'keras_available' in data
        assert 'onnx_available' in data
        assert 'deepface_available' in data
        
        assert data['status'] == 'healthy'
        assert isinstance(data['keras_available'], bool)
        assert isinstance(data['onnx_available'], bool)
        assert isinstance(data['deepface_available'], bool)


class TestCameraEndpoint:
    """Tests for the /api/cameras endpoint"""
    
    def test_cameras_endpoint_exists(self, client):
        """Test that cameras endpoint is accessible"""
        response = client.get('/api/cameras')
        assert response.status_code == 200
    
    def test_cameras_endpoint_returns_json(self, client):
        """Test that cameras endpoint returns JSON"""
        response = client.get('/api/cameras')
        assert response.content_type == 'application/json'
    
    def test_cameras_endpoint_structure(self, client):
        """Test that cameras endpoint returns expected fields"""
        response = client.get('/api/cameras')
        data = json.loads(response.data)
        
        assert 'cameras' in data
        assert 'current' in data
        assert 'recommended' in data
        
        assert isinstance(data['cameras'], list)
        assert isinstance(data['current'], int)
        assert isinstance(data['recommended'], int)
    
    def test_camera_list_structure(self, client):
        """Test that each camera in the list has expected fields"""
        response = client.get('/api/cameras')
        data = json.loads(response.data)
        
        for camera in data['cameras']:
            assert 'index' in camera
            assert 'name' in camera
            assert 'working' in camera
            
            assert isinstance(camera['index'], int)
            assert isinstance(camera['name'], str)
            assert isinstance(camera['working'], bool)


class TestModelsEndpoint:
    """Tests for the /api/models endpoint"""
    
    def test_models_endpoint_exists(self, client):
        """Test that models endpoint is accessible"""
        response = client.get('/api/models')
        assert response.status_code == 200
    
    def test_models_endpoint_returns_json(self, client):
        """Test that models endpoint returns JSON"""
        response = client.get('/api/models')
        assert response.content_type == 'application/json'
    
    def test_models_endpoint_structure(self, client):
        """Test that models endpoint returns expected fields"""
        response = client.get('/api/models')
        data = json.loads(response.data)
        
        assert 'models' in data
        assert 'current' in data
        
        assert isinstance(data['models'], list)
        assert isinstance(data['current'], str)
    
    def test_model_list_structure(self, client):
        """Test that each model in the list has expected fields"""
        response = client.get('/api/models')
        data = json.loads(response.data)
        
        for model in data['models']:
            assert 'id' in model
            assert 'name' in model
            assert 'available' in model
            
            assert isinstance(model['id'], str)
            assert isinstance(model['name'], str)
            assert isinstance(model['available'], bool)
    
    def test_model_ids(self, client):
        """Test that expected model IDs are present"""
        response = client.get('/api/models')
        data = json.loads(response.data)
        
        model_ids = [model['id'] for model in data['models']]
        
        assert 'deepface' in model_ids
        assert 'onnx' in model_ids
        assert 'keras' in model_ids


class TestSettingsEndpoint:
    """Tests for the /api/settings endpoint"""
    
    def test_settings_endpoint_post_only(self, client):
        """Test that settings endpoint only accepts POST"""
        response = client.get('/api/settings')
        assert response.status_code == 405  # Method not allowed
    
    def test_update_camera_setting(self, client):
        """Test updating camera setting"""
        response = client.post('/api/settings',
                              data=json.dumps({'camera_index': 0}),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'camera_index' in data
        assert 'model_type' in data
        assert data['camera_index'] == 0
    
    def test_update_model_setting(self, client):
        """Test updating model setting"""
        # First check which models are available
        models_response = client.get('/api/models')
        models_data = json.loads(models_response.data)
        
        available_model = None
        for model in models_data['models']:
            if model['available']:
                available_model = model['id']
                break
        
        if available_model:
            response = client.post('/api/settings',
                                  data=json.dumps({'model_type': available_model}),
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'model_type' in data
            assert data['model_type'] == available_model
    
    def test_update_invalid_model(self, client):
        """Test updating to an invalid model"""
        response = client.post('/api/settings',
                              data=json.dumps({'model_type': 'invalid_model'}),
                              content_type='application/json')
        
        assert response.status_code == 400


class TestPredictEndpoint:
    """Tests for the /predict endpoint"""
    
    def test_predict_endpoint_post_only(self, client):
        """Test that predict endpoint only accepts POST"""
        response = client.get('/predict')
        assert response.status_code == 405  # Method not allowed
    
    def test_predict_no_file(self, client):
        """Test predict endpoint with no file"""
        response = client.post('/predict')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_predict_empty_filename(self, client):
        """Test predict endpoint with empty filename"""
        response = client.post('/predict',
                              data={'file': (io.BytesIO(b''), '')})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_predict_with_image(self, client, sample_face_image):
        """Test predict endpoint with a valid image"""
        response = client.post('/predict',
                              data={'file': (sample_face_image, 'test.png')},
                              content_type='multipart/form-data')
        
        # Response might be 200 (face detected), 400 (no face detected), or 500 (processing error)
        # All are valid responses depending on model availability and image quality
        assert response.status_code in [200, 400, 500]
        
        data = json.loads(response.data)
        
        if response.status_code == 200:
            # If face detected, check response structure
            assert 'success' in data
            assert 'prediction' in data
            assert 'confidence' in data
            assert 'box' in data
            assert 'all_predictions' in data
            
            assert data['success'] is True
            assert isinstance(data['prediction'], str)
            assert isinstance(data['confidence'], (int, float))
            assert 0 <= data['confidence'] <= 1
            
            if data['box']:
                assert isinstance(data['box'], list)
                assert len(data['box']) == 4  # [x, y, w, h]
            
            assert isinstance(data['all_predictions'], list)
        elif response.status_code == 400:
            # If no face detected
            assert 'error' in data or 'success' in data
        else:  # 500
            # Processing error (e.g., model failed to process image)
            assert 'error' in data


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_enumerate_cameras_returns_list(self):
        """Test that enumerate_cameras returns a list"""
        cameras = emotion_app.enumerate_cameras(max_cameras=3)
        assert isinstance(cameras, list)
    
    def test_camera_structure(self):
        """Test that each camera has expected structure"""
        cameras = emotion_app.enumerate_cameras(max_cameras=3)
        
        for camera in cameras:
            assert 'index' in camera
            assert 'name' in camera
            assert 'working' in camera
    
    def test_draw_rounded_rectangle(self):
        """Test that draw_rounded_rectangle doesn't crash"""
        # Create a test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # This should not raise an exception
        try:
            emotion_app.draw_rounded_rectangle(
                img, (10, 10), (50, 50), (255, 255, 0), 2, 5
            )
            assert True
        except Exception as e:
            pytest.fail(f"draw_rounded_rectangle raised exception: {e}")


class TestEmotionLabels:
    """Tests for emotion labels"""
    
    def test_emotion_labels_exist(self):
        """Test that EMOTION_LABELS is defined"""
        assert hasattr(emotion_app, 'EMOTION_LABELS')
    
    def test_emotion_labels_count(self):
        """Test that there are 7 emotion labels"""
        assert len(emotion_app.EMOTION_LABELS) == 7
    
    def test_emotion_labels_content(self):
        """Test that expected emotions are in the list"""
        expected_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
        
        for emotion in expected_emotions:
            assert emotion in emotion_app.EMOTION_LABELS


class TestModelLoading:
    """Tests for model loading"""
    
    def test_at_least_one_model_available(self):
        """Test that at least one model is available"""
        has_model = (
            emotion_app.KERAS_MODEL is not None or
            emotion_app.ONNX_SESSION is not None or
            emotion_app.DEEPFACE_AVAILABLE
        )
        
        assert has_model, "At least one model should be available"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
