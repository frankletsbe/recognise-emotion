# Tests for Emotion Recognition App

This directory contains comprehensive tests for the emotion recognition Flask application.

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=html
```

### Run Specific Test Classes

```bash
# Test only health endpoint
pytest tests/test_app.py::TestHealthEndpoint -v

# Test only camera endpoint
pytest tests/test_app.py::TestCameraEndpoint -v

# Test only prediction endpoint
pytest tests/test_app.py::TestPredictEndpoint -v
```

### Run Specific Tests

```bash
# Test a single function
pytest tests/test_app.py::TestHealthEndpoint::test_health_endpoint_exists -v
```

## Test Coverage

The test suite covers:

### 1. **Health Endpoint** (`/health`)

- Endpoint accessibility
- JSON response format
- Response structure validation
- Model availability reporting

### 2. **Camera Endpoint** (`/api/cameras`)

- Endpoint accessibility
- JSON response format
- Camera list structure
- Camera detection functionality

### 3. **Models Endpoint** (`/api/models`)

- Endpoint accessibility
- JSON response format
- Model list structure
- Model availability checking
- Expected model IDs (deepface, onnx, keras)

### 4. **Settings Endpoint** (`/api/settings`)

- POST-only validation
- Camera index updates
- Model type updates
- Invalid model rejection

### 5. **Predict Endpoint** (`/predict`)

- POST-only validation
- File upload validation
- Empty filename handling
- Image processing
- Response structure validation
- Emotion prediction accuracy

### 6. **Utility Functions**

- `enumerate_cameras()` functionality
- `draw_rounded_rectangle()` error handling
- Camera structure validation

### 7. **Emotion Labels**

- Label existence
- Correct count (7 emotions)
- Expected emotion names

### 8. **Model Loading**

- At least one model available
- Model initialization

## Test Structure

```
tests/
├── __init__.py          # Package initialization
├── test_app.py          # Main test suite
└── README.md            # This file
```

## Continuous Integration

Tests are automatically run on every commit via GitHub Actions. See `.github/workflows/test.yml` for configuration.

### CI Pipeline

1. **Matrix Testing**: Tests run on Python 3.9, 3.10, and 3.11
2. **System Dependencies**: Installs OpenCV dependencies
3. **Python Dependencies**: Installs all requirements
4. **Test Execution**: Runs pytest with coverage
5. **Coverage Upload**: Uploads to Codecov
6. **App Startup Test**: Verifies app can start

## Expected Test Results

When all models are available:

```
========== test session starts ==========
collected 35 items

tests/test_app.py::TestHealthEndpoint::test_health_endpoint_exists PASSED
tests/test_app.py::TestHealthEndpoint::test_health_endpoint_returns_json PASSED
tests/test_app.py::TestHealthEndpoint::test_health_endpoint_structure PASSED
tests/test_app.py::TestCameraEndpoint::test_cameras_endpoint_exists PASSED
...
========== 35 passed in 5.23s ==========
```

## Writing New Tests

### Test Class Template

```python
class TestNewFeature:
    """Tests for new feature"""

    def test_feature_exists(self, client):
        """Test that feature is accessible"""
        response = client.get('/new-endpoint')
        assert response.status_code == 200

    def test_feature_functionality(self, client):
        """Test feature works correctly"""
        # Your test code here
        pass
```

### Using Fixtures

```python
def test_with_sample_image(self, client, sample_face_image):
    """Test using the sample face image fixture"""
    response = client.post('/predict',
                          data={'file': (sample_face_image, 'test.png')},
                          content_type='multipart/form-data')
    assert response.status_code == 200
```

## Troubleshooting

### Tests Fail Due to Missing Models

If tests fail because models aren't available, this is expected. The tests are designed to handle missing models gracefully.

### OpenCV Errors on Linux

If you get OpenCV errors on Linux, install system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### Import Errors

Make sure you're running tests from the project root:

```bash
cd /path/to/recognise-expression
pytest tests/ -v
```

## Coverage Goals

- **Target**: 80%+ code coverage
- **Current**: Run `pytest --cov=. --cov-report=term` to see current coverage
- **HTML Report**: Run `pytest --cov=. --cov-report=html` and open `htmlcov/index.html`

## Best Practices

1. **Run tests before committing**: `pytest tests/ -v`
2. **Check coverage**: `pytest tests/ --cov=.`
3. **Test new features**: Add tests for any new endpoints or functions
4. **Keep tests fast**: Mock external dependencies when possible
5. **Use descriptive names**: Test names should describe what they test

## Integration with Git

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Flask testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
