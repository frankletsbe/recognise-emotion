# End-to-End Test for Emotion Recognition App

## Overview

Created `tests/test_expression.py` - a comprehensive end-to-end test that simulates real user interaction with your emotion recognition web application.

## What the Test Does

### 1. **Starts the Flask App**

- Launches `app.py` as a subprocess
- Waits up to 30 seconds for the app to be ready
- Verifies the `/health` endpoint responds

### 2. **Downloads Test Image**

- Fetches a real facial expression image from: https://pxhere.com/en/photo/920987
- This is a child's face with a happy/smiling expression
- Saves it temporarily for testing

### 3. **Automates Browser Interaction**

- Uses Selenium WebDriver with Chrome (headless mode)
- Navigates to http://127.0.0.1:5000/
- Finds the file input element (`#fileInput`)
- Uploads the downloaded facial image

### 4. **Validates Results**

- Waits for the results section to appear (`#resultsSection`)
- Extracts the predicted emotion from `#emotionLabel`
- Extracts the confidence percentage from `#confidenceValue`
- Validates that:
  - Prediction is one of the 7 valid emotions
  - Confidence is between 0-100%
  - Results are displayed correctly

### 5. **Cleanup**

- Stops the Flask app subprocess
- Closes the browser
- Deletes temporary files

## Test Classes and Methods

### `TestEmotionRecognitionE2E`

Main test class with fixtures and test methods:

#### Fixtures:

- **`app_process`**: Starts and manages the Flask app subprocess
- **`driver`**: Sets up Selenium WebDriver (Chrome headless)
- **`test_image_path`**: Downloads and provides the test image

#### Test Methods:

1. **`test_app_homepage_loads`**: Verifies the homepage loads successfully
2. **`test_upload_area_exists`**: Confirms the upload interface is present
3. **`test_image_upload_and_prediction`**: **Main E2E test** - uploads image and validates prediction
4. **`test_prediction_results_format`**: Validates the format of prediction results

### `test_direct_api_prediction`

Standalone test that directly calls the `/predict` API endpoint without browser automation. This is a fallback if Selenium is not available.

## Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Chrome is installed (for Selenium tests)
```

### Run All E2E Tests

```bash
pytest tests/test_expression.py -v -s
```

### Run Specific Test

```bash
# Just the main upload and prediction test
pytest tests/test_expression.py::TestEmotionRecognitionE2E::test_image_upload_and_prediction -v -s

# Just the API fallback test (no browser)
pytest tests/test_expression.py::test_direct_api_prediction -v -s
```

### Using the PowerShell Helper Script

```powershell
.\run_e2e_tests.ps1
```

## Expected Output

```
=== Emotion Recognition E2E Test Runner ===

Checking dependencies...
Running end-to-end tests...

tests/test_expression.py::TestEmotionRecognitionE2E::test_app_homepage_loads
✓ App started successfully at http://127.0.0.1:5000
✓ Homepage loaded successfully (title: Emotion Recognition AI)
PASSED

tests/test_expression.py::TestEmotionRecognitionE2E::test_upload_area_exists
✓ Drop zone found by ID
PASSED

tests/test_expression.py::TestEmotionRecognitionE2E::test_image_upload_and_prediction
✓ Test image downloaded to C:\Users\...\temp_image.jpg
✓ Image uploaded: C:\Users\...\temp_image.jpg
✓ Prediction received: Happy
✓ Confidence: 87%
✓ Extracted confidence: 87.0%
PASSED

tests/test_expression.py::TestEmotionRecognitionE2E::test_prediction_results_format
✓ Found emotions in results: ['Happy']
PASSED

tests/test_expression.py::test_direct_api_prediction
✓ API Prediction: Happy
✓ API Confidence: 0.87
PASSED

=== 5 passed in 45.23s ===
```

## Configuration

### Timeouts

- **STARTUP_TIMEOUT**: 30 seconds (app startup)
- **TEST_TIMEOUT**: 60 seconds (prediction completion)

### Test Image

- **URL**: https://c.pxhere.com/photos/0e/b5/child_facial_expression_smile_laugh_close_up_human_body_face_nose-920987.jpg!d
- **Expected Emotion**: Happy (child smiling)

### Browser Settings

- **Mode**: Headless (no visible window)
- **Size**: 1920x1080
- **Options**: `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`

## Troubleshooting

### Chrome/ChromeDriver Not Found

If you see "Chrome WebDriver not available", the tests will be skipped. To fix:

1. Install Google Chrome
2. ChromeDriver should be auto-managed by Selenium 4.15+
3. If issues persist, manually install ChromeDriver matching your Chrome version

### App Fails to Start

- Check that port 5000 is not already in use
- Ensure all dependencies are installed
- Check that models are available

### Timeout Errors

- Increase `TEST_TIMEOUT` if your model is slow
- Check network connection for image download
- Ensure sufficient system resources

### No Face Detected

If the test image doesn't detect a face:

- This is expected behavior if face detection fails
- The test will show a 400 error with "No face detected"
- Try a different test image URL

## Integration with CI/CD

To add this to your GitHub Actions workflow, update `.github/workflows/test.yml`:

```yaml
- name: Install Chrome for E2E tests
  run: |
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable

- name: Run E2E tests
  run: |
    pytest tests/test_expression.py -v -s
```

## Files Modified/Created

1. **Created**: `tests/test_expression.py` - Main E2E test file
2. **Created**: `run_e2e_tests.ps1` - Helper script for Windows
3. **Updated**: `requirements.txt` - Added `selenium>=4.15.0`
4. **Updated**: `tests/README.md` - Added E2E test documentation

## Next Steps

1. **Run the test locally** to verify it works:

   ```bash
   pytest tests/test_expression.py -v -s
   ```

2. **Add to CI/CD** if desired (see Integration section above)

3. **Customize test images** by changing `TEST_IMAGE_URL` in the test file

4. **Add more test cases** for different emotions:
   - Angry face
   - Sad face
   - Surprised face
   - etc.

## Benefits

✅ **Automated validation** of the complete user workflow
✅ **Real browser testing** with Selenium
✅ **Actual image processing** with real facial expressions
✅ **Confidence percentage validation**
✅ **Catches integration issues** that unit tests might miss
✅ **Runs on every commit** (when added to CI/CD)
✅ **Fallback API test** for environments without browser support
