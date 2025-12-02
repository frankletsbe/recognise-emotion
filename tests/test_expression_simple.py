"""
Simple end-to-end test for emotion recognition app.

This test uses direct HTTP requests instead of Selenium for faster,
more reliable testing without browser dependencies.

It starts its own instance of the app on port 5001 to avoid conflicts.
"""

import pytest
import requests
import tempfile
import os
import time
import subprocess
import sys
import signal
from pathlib import Path

# Test configuration
TEST_PORT = 5001
APP_URL = f"http://127.0.0.1:{TEST_PORT}"

# List of test images to try (in case one fails or is removed)
TEST_IMAGE_URLS = [
    # Person with more background (to avoid whole-image detection filter)
    "https://images.unsplash.com/photo-1542206395-9feb3edaa68d?w=800&q=80",
    # Happy child
    "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800&q=80",
    # Professional woman smiling
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80",
]


@pytest.fixture(scope="class")
def app_process():
    """Start the Flask app as a subprocess on a test port"""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    app_path = project_root / "app.py"
    
    print(f"\n🚀 Starting app on port {TEST_PORT}...")
    
    # Start the Flask app
    env = os.environ.copy()
    env['PORT'] = str(TEST_PORT)
    env['DEBUG'] = 'false'
    env['SKIP_CAMERAS'] = 'true'
    
    # Use python executable from current environment
    python_exe = sys.executable
    
    process = subprocess.Popen(
        [python_exe, str(app_path)],
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the app to start
    start_time = time.time()
    app_ready = False
    
    while time.time() - start_time < 15:  # 15s timeout
        try:
            response = requests.get(f"{APP_URL}/health", timeout=1)
            if response.status_code == 200:
                app_ready = True
                print(f"✓ App started successfully at {APP_URL}")
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
            
        # Check if process died
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ App process died unexpectedly!")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            break
    
    if not app_ready:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=2)
        pytest.fail(f"Flask app failed to start within 15 seconds on port {TEST_PORT}")
    
    yield process
    
    # Cleanup: terminate the app
    print("\n🛑 Stopping app...")
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


class TestEmotionRecognitionSimple:
    """Simple API-based tests for emotion recognition"""
    
    @pytest.fixture(scope="class")
    def test_image_path(self):
        """Download a test image (trying multiple URLs if needed)"""
        temp_path = None
        success = False
        
        for url in TEST_IMAGE_URLS:
            try:
                print(f"\n📥 Downloading test image from {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(response.content)
                    temp_path = f.name
                
                print(f"✓ Test image downloaded ({len(response.content)} bytes)")
                success = True
                break
            except Exception as e:
                print(f"⚠ Failed to download {url}: {e}")
                continue
        
        if not success:
            pytest.skip("Failed to download any test images")
            
        yield temp_path
        
        # Cleanup
        if temp_path:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_health_check(self, app_process):
        """Test that the app is running and healthy"""
        response = requests.get(f"{APP_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        print(f"✓ App is healthy")
        print(f"  - Keras: {data.get('keras_available', False)}")
        print(f"  - ONNX: {data.get('onnx_available', False)}")
        print(f"  - DeepFace: {data.get('deepface_available', False)}")
    
    def test_predict_with_facial_image(self, app_process, test_image_path):
        """
        Main test: Upload a facial image and validate emotion prediction
        """
        print(f"\n🎭 Testing emotion prediction...")
        
        # Upload the image
        with open(test_image_path, 'rb') as img_file:
            files = {'file': ('test_face.jpg', img_file, 'image/jpeg')}
            response = requests.post(f"{APP_URL}/predict", files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        # Parse response
        data = response.json()
        
        if response.status_code == 200:
            # Success - face detected and emotion predicted
            assert 'prediction' in data or 'emotion' in data, "No prediction in response"
            assert 'confidence' in data, "No confidence in response"
            
            prediction = data.get('prediction') or data.get('emotion')
            confidence = data.get('confidence')
            
            # Validate prediction is a valid emotion
            valid_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
            assert prediction in valid_emotions, f"Invalid emotion: {prediction}"
            
            # Validate confidence is in valid range (0-1 or 0-100)
            if confidence <= 1.0:
                confidence_pct = confidence * 100
            else:
                confidence_pct = confidence
            
            assert 0 <= confidence_pct <= 100, f"Confidence {confidence_pct}% is out of range"
            
            # Print results
            print(f"\n✅ PREDICTION SUCCESSFUL")
            print(f"   Emotion: {prediction}")
            print(f"   Confidence: {confidence_pct:.1f}%")
            
            # Print all predictions if available
            if 'all_predictions' in data:
                print(f"\n   All predictions:")
                for pred in data['all_predictions']:
                    emotion = pred.get('emotion', 'Unknown')
                    conf = pred.get('confidence', 0)
                    if conf <= 1.0:
                        conf *= 100
                    print(f"     - {emotion}: {conf:.1f}%")
            
        elif response.status_code == 400:
            # No face detected or validation error
            error_msg = data.get('error', 'Unknown error')
            
            if 'no face' in error_msg.lower():
                pytest.fail(f"No face detected in test image. Error: {error_msg}")
            else:
                pytest.fail(f"Validation error: {error_msg}")
        
        else:
            # Server error
            error_msg = data.get('error', 'Unknown error')
            pytest.fail(f"Server error ({response.status_code}): {error_msg}")
    
    def test_predict_without_file(self, app_process):
        """Test that prediction fails gracefully without a file"""
        response = requests.post(f"{APP_URL}/predict", timeout=5)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        print(f"✓ Correctly rejected request without file")
    
    def test_models_endpoint(self, app_process):
        """Test that models endpoint returns available models"""
        response = requests.get(f"{APP_URL}/api/models", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert 'models' in data
        assert 'current' in data
        
        print(f"✓ Available models:")
        for model in data['models']:
            status = "✓" if model['available'] else "✗"
            print(f"  {status} {model['name']} ({model['id']})")
        
        print(f"  Current: {data['current']}")

    def test_cameras_endpoint(self, app_process):
        """Test that cameras endpoint returns camera list"""
        response = requests.get(f"{APP_URL}/api/cameras", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert 'cameras' in data
        
        print(f"✓ Detected cameras: {len(data['cameras'])}")
        for cam in data['cameras']:
            print(f"  - Index {cam['index']}: {cam['name']} (Working: {cam['working']})")


if __name__ == '__main__':
    # Run with: python tests/test_expression_simple.py
    pytest.main([__file__, '-v', '-s'])
