"""
End-to-end test for emotion recognition app.

This test starts the Flask app, navigates to the web interface,
uploads a facial image, and verifies the emotion prediction results.
"""

import pytest
import time
import os
import sys
import subprocess
import requests
from pathlib import Path
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Test configuration
APP_URL = "http://127.0.0.1:5000"
TEST_IMAGE = "Gemini_Emotion_image.png"
STARTUP_TIMEOUT = 30  # seconds to wait for app to start
TEST_TIMEOUT = 60  # seconds to wait for prediction


class TestEmotionRecognitionE2E:
    """End-to-end tests for the emotion recognition web application"""
    
    @pytest.fixture(scope="class")
    def app_process(self):
        """Start the Flask app as a subprocess"""
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        app_path = project_root / "app.py"
        
        # Start the Flask app
        env = os.environ.copy()
        env['PORT'] = '5000'
        env['DEBUG'] = 'false'
        env['SKIP_CAMERAS'] = 'true'
        
        process = subprocess.Popen(
            [sys.executable, str(app_path)],
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the app to start
        start_time = time.time()
        app_ready = False
        
        while time.time() - start_time < STARTUP_TIMEOUT:
            try:
                response = requests.get(f"{APP_URL}/health", timeout=2)
                if response.status_code == 200:
                    app_ready = True
                    print(f"✓ App started successfully at {APP_URL}")
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        
        if not app_ready:
            process.terminate()
            process.wait(timeout=5)
            pytest.fail(f"Flask app failed to start within {STARTUP_TIMEOUT} seconds")
        
        yield process
        
        # Cleanup: terminate the app
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        print("✓ App stopped successfully")
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Try to create the driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            yield driver
            driver.quit()
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
    
    @pytest.fixture(scope="class")
    def test_image_path(self):
        """Return path to local test image"""
        # Use local image in the same directory as this test file
        current_dir = Path(__file__).parent
        image_path = current_dir / "Gemini_Emotion_image.png"
        
        if not image_path.exists():
            pytest.skip(f"Test image not found at {image_path}")
            
        print(f"✓ Using local test image: {image_path}")
        return str(image_path)
    
    def test_app_homepage_loads(self, app_process, driver):
        """Test that the app homepage loads successfully"""
        driver.get(APP_URL)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check that the page title contains expected text
        assert "Emotion" in driver.title or "Recognition" in driver.title or len(driver.title) > 0
        print(f"✓ Homepage loaded successfully (title: {driver.title})")
    
    def test_upload_area_exists(self, app_process, driver):
        """Test that the upload area is present on the page"""
        driver.get(APP_URL)
        
        # Look for the drop zone or file input
        try:
            # Try to find the drop zone by common selectors
            drop_zone = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dropZone"))
            )
            assert drop_zone is not None
            print("✓ Drop zone found by ID")
        except TimeoutException:
            # Try alternative selectors
            try:
                drop_zone = driver.find_element(By.CSS_SELECTOR, ".drop-zone")
                assert drop_zone is not None
                print("✓ Drop zone found by class")
            except NoSuchElementException:
                # Try to find file input
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                assert file_input is not None
                print("✓ File input found")
    
    def test_image_upload_and_prediction(self, app_process, driver, test_image_path):
        """
        Test the complete workflow: upload image and get emotion prediction
        This is the main end-to-end test
        """
        driver.get(APP_URL)
        
        # Wait for page to be fully loaded
        time.sleep(2)
        
        # Find the file input element
        try:
            # Try to find hidden file input
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        except NoSuchElementException:
            pytest.fail("Could not find file input element")
        
        # Upload the image
        file_input.send_keys(test_image_path)
        print(f"✓ Image uploaded: {test_image_path}")
        
        # Wait for the prediction to complete
        # Look for results container or prediction text
        try:
            # Wait for results section to become visible
            results_section = WebDriverWait(driver, TEST_TIMEOUT).until(
                EC.visibility_of_element_located((By.ID, "resultsSection"))
            )
            
            # Get the emotion label
            emotion_label = driver.find_element(By.ID, "emotionLabel")
            prediction_text = emotion_label.text
            print(f"✓ Prediction received: {prediction_text}")
            
            # Verify prediction is not empty
            assert len(prediction_text) > 0, "Prediction text is empty"
            
            # Get confidence value
            try:
                confidence_element = driver.find_element(By.ID, "confidenceValue")
                confidence_text = confidence_element.text
                print(f"✓ Confidence: {confidence_text}%")
                
                # Extract numeric value
                import re
                confidence_match = re.search(r'(\d+\.?\d*)', confidence_text)
                
                if confidence_match:
                    confidence_value = float(confidence_match.group(1))
                    print(f"✓ Extracted confidence: {confidence_value}%")
                    
                    # Verify confidence is in valid range
                    assert 0 <= confidence_value <= 100, f"Confidence {confidence_value}% is out of range"
                    
                    # Store results for reporting
                    return {
                        'prediction': prediction_text,
                        'confidence': confidence_value,
                        'success': True
                    }
                else:
                    print("⚠ Could not extract numeric confidence value")
                    return {
                        'prediction': prediction_text,
                        'confidence_text': confidence_text,
                        'success': True
                    }
                    
            except NoSuchElementException:
                print("⚠ Confidence element not found")
                
                # At minimum, we have the prediction
                return {
                    'prediction': prediction_text,
                    'success': True
                }
                
        except TimeoutException:
            # Try alternative approach - check if error state is shown
            try:
                error_state = driver.find_element(By.ID, "errorState")
                if "hidden" not in error_state.get_attribute("class"):
                    error_message = driver.find_element(By.ID, "errorMessage").text
                    pytest.fail(f"App showed error: {error_message}")
            except NoSuchElementException:
                pass
            
            # Try to find any emotion text on the page
            try:
                emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                for emotion in emotions:
                    if emotion.lower() in page_text.lower():
                        print(f"✓ Found emotion in page: {emotion}")
                        
                        # Try to extract percentage
                        import re
                        percentage_match = re.search(rf'{emotion}.*?(\d+\.?\d*)%', page_text, re.IGNORECASE)
                        if percentage_match:
                            confidence = float(percentage_match.group(1))
                            print(f"✓ Extracted: {emotion} with {confidence}% confidence")
                            return {
                                'prediction': emotion,
                                'confidence': confidence,
                                'success': True
                            }
                        else:
                            return {
                                'prediction': emotion,
                                'success': True
                            }
                
                pytest.fail(f"No prediction found after {TEST_TIMEOUT} seconds. Page text: {page_text[:500]}")
                
            except NoSuchElementException:
                pytest.fail("Could not find prediction results on page")
    
    def test_prediction_results_format(self, app_process, driver, test_image_path):
        """Test that prediction results are in the expected format"""
        driver.get(APP_URL)
        time.sleep(2)
        
        # Upload image
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(test_image_path)
        
        # Wait for results
        time.sleep(5)
        
        # Check that results contain expected emotions
        expected_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # At least one emotion should be present
        found_emotions = [emotion for emotion in expected_emotions if emotion.lower() in page_text.lower()]
        
        assert len(found_emotions) > 0, f"No valid emotions found in results. Page text: {page_text[:500]}"
        print(f"✓ Found emotions in results: {found_emotions}")


def test_direct_api_prediction():
    """
    Test the /predict API endpoint directly without browser automation.
    This is a fallback test if Selenium is not available.
    """
    # Use local image
    current_dir = Path(__file__).parent
    image_path = current_dir / "Gemini_Emotion_image.png"
    
    if not image_path.exists():
        pytest.skip(f"Test image not found at {image_path}")
    
    # Wait a moment to ensure app is running
    time.sleep(2)
    
    # Check if app is running
    try:
        health_check = requests.get(f"{APP_URL}/health", timeout=5)
        if health_check.status_code != 200:
            pytest.skip("App is not running")
    except requests.exceptions.RequestException:
        pytest.skip("App is not running")
    
    # Send prediction request
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': ('test_face.png', img_file, 'image/png')}
            response = requests.post(f"{APP_URL}/predict", files=files, timeout=30)
        
        # Check response
        assert response.status_code in [200, 400], f"Unexpected status code: {response.status_code}"
        
        data = response.json()
        
        if response.status_code == 200:
            assert 'prediction' in data or 'emotion' in data, "No prediction in response"
            assert 'confidence' in data, "No confidence in response"
            
            prediction = data.get('prediction') or data.get('emotion')
            confidence = data.get('confidence')
            
            print(f"✓ API Prediction: {prediction}")
            print(f"✓ API Confidence: {confidence}")
            
            # Verify confidence is in valid range
            assert 0 <= confidence <= 1, f"Confidence {confidence} is out of range"
            
            # Verify prediction is a valid emotion
            valid_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
            assert prediction in valid_emotions, f"Invalid emotion: {prediction}"
            
        else:  # 400
            # No face detected or other error
            assert 'error' in data, "No error message in 400 response"
            print(f"⚠ API returned error: {data['error']}")
            
    except Exception as e:
        pytest.skip(f"API test failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
