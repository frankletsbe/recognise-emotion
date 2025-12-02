// Emotion emoji mapping
const EMOTION_EMOJIS = {
    'Angry': '😠',
    'Disgust': '🤢',
    'Fear': '😨',
    'Happy': '😊',
    'Neutral': '😐',
    'Sad': '😢',
    'Surprise': '😲'
};

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const clearButton = document.getElementById('clearButton');
const resultsSection = document.getElementById('resultsSection');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const retryButton = document.getElementById('retryButton');
const emotionIcon = document.getElementById('emotionIcon');
const emotionLabel = document.getElementById('emotionLabel');
const confidenceValue = document.getElementById('confidenceValue');
const predictionsList = document.getElementById('predictionsList');

// Webcam Elements
const startWebcamBtn = document.getElementById('startWebcamBtn');
const webcamSection = document.getElementById('webcamSection');
const webcamVideo = document.getElementById('webcamVideo');
const webcamCanvas = document.getElementById('webcamCanvas');
const stopWebcamBtn = document.getElementById('stopWebcamBtn');

// Settings Elements
const cameraSelect = document.getElementById('cameraSelect');
const modelSelect = document.getElementById('modelSelect');

// State
let currentFile = null;
let stream = null;
let isProcessing = false;
let animationFrameId = null;
let availableCameras = [];
let availableModels = [];

// Initialize
function init() {
    setupEventListeners();
    loadCameras();
    loadModels();
}

function setupEventListeners() {
    // Drop zone click
    dropZone.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    // Clear button
    clearButton.addEventListener('click', clearImage);
    
    // Retry button
    retryButton.addEventListener('click', () => {
        hideError();
        if (currentFile) {
            uploadAndPredict(currentFile);
        }
    });
    
    // Prevent default drag behavior on document
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => e.preventDefault());

    // Webcam events
    startWebcamBtn.addEventListener('click', startWebcam);
    stopWebcamBtn.addEventListener('click', stopWebcam);
    
    // Settings events
    cameraSelect.addEventListener('change', handleCameraChange);
    modelSelect.addEventListener('change', handleModelChange);
}

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please upload an image file');
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('Image size should be less than 10MB');
        return;
    }
    
    currentFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        showPreview();
    };
    reader.readAsDataURL(file);
    
    // Upload and predict
    uploadAndPredict(file);
}

function showPreview() {
    previewSection.classList.remove('hidden');
    hideResults();
    hideError();
}

function clearImage() {
    currentFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewSection.classList.add('hidden');
    hideResults();
    hideError();
    hideLoading();
    hideLoading();
}

async function loadCameras() {
    try {
        const response = await fetch('/api/cameras');
        const data = await response.json();
        
        availableCameras = data.cameras;
        cameraSelect.innerHTML = '';
        
        data.cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera.index;
            option.textContent = `${camera.name}${camera.working ? ' ✓' : ' (not working)'}`;
            if (camera.index === data.recommended) {
                option.selected = true;
            }
            if (!camera.working) {
                option.style.color = '#888';
            }
            cameraSelect.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to load cameras:', err);
        cameraSelect.innerHTML = '<option>Error loading cameras</option>';
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        availableModels = data.models;
        modelSelect.innerHTML = '';
        
        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name + (model.available ? '' : ' (unavailable)');
            if (model.id === data.current) {
                option.selected = true;
            }
            if (!model.available) {
                option.disabled = true;
                option.style.color = '#888';
            }
            modelSelect.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to load models:', err);
        modelSelect.innerHTML = '<option>Error loading models</option>';
    }
}

async function handleCameraChange() {
    const cameraIndex = parseInt(cameraSelect.value);
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ camera_index: cameraIndex })
        });
        
        if (response.ok) {
            console.log('Camera updated to index:', cameraIndex);
            // If webcam is running, restart it with new camera
            if (stream) {
                stopWebcam();
                setTimeout(() => startWebcam(), 500);
            }
        }
    } catch (err) {
        console.error('Failed to update camera:', err);
    }
}

async function handleModelChange() {
    const modelType = modelSelect.value;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model_type: modelType })
        });
        
        if (response.ok) {
            console.log('Model updated to:', modelType);
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to update model');
        }
    } catch (err) {
        console.error('Failed to update model:', err);
        showError('Failed to update model');
    }
}

async function startWebcam(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcamVideo.srcObject = stream;
        
        // CRITICAL FIX: Wait for video to actually start playing
        await webcamVideo.play();
        
        dropZone.classList.add('hidden');
        previewSection.classList.add('hidden');
        webcamSection.classList.remove('hidden');
        hideResults();
        hideError();
        
        console.log('Webcam started, video playing:', !webcamVideo.paused); // Debug
        
        // Start real-time processing loop
        processWebcamFrame();
        
    } catch (err) {
        console.error("Error accessing webcam:", err);
        showError("Could not access webcam. Please allow camera permissions.");
    }
}

async function processWebcamFrame() {
    console.log('processWebcamFrame called, stream:', !!stream); // Debug
    
    if (!stream || webcamVideo.paused || webcamVideo.ended) {
        console.log('Stream check failed'); // Debug
        return;
    }
    
    // Check if video is ready
    if (webcamVideo.readyState !== webcamVideo.HAVE_ENOUGH_DATA) {
        console.log('Video not ready yet'); // Debug
        animationFrameId = requestAnimationFrame(processWebcamFrame);
        return;
    }

    console.log('About to process frame, isProcessing:', isProcessing); // Debug

    if (!isProcessing) {
        isProcessing = true;
        
        // Capture frame
        const canvas = document.createElement('canvas');
        canvas.width = webcamVideo.videoWidth;
        canvas.height = webcamVideo.videoHeight;
        const ctx = canvas.getContext('2d');
        
        console.log('Canvas size:', canvas.width, 'x', canvas.height); // Debug
        
        // Draw video to off-screen canvas (raw, unmirrored)
        ctx.drawImage(webcamVideo, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(async (blob) => {
            if (blob) {
                console.log('Blob created, sending to server...'); // Debug
                const formData = new FormData();
                formData.append('file', new File([blob], "frame.jpg", { type: "image/jpeg" }));
                
                try {
                    const response = await fetch('/predict', {
                        method: 'POST',
                        body: formData
                    });
                    
                    console.log('Response status:', response.status); // Debug
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('Prediction response:', data); // Debug log
                        if (data.success && data.box) {
                            console.log('Drawing box at:', data.box); // Debug log
                            drawOverlay(data, canvas.width, canvas.height);
                            displayResults(data); // Update sidebar results too
                        } else {
                            console.log('No box in response or not successful'); // Debug log
                        }
                    } else {
                        console.error('Response not OK:', response.status);
                    }
                } catch (err) {
                    console.error("Frame processing error:", err);
                } finally {
                    isProcessing = false;
                }
            } else {
                console.log('Blob creation failed'); // Debug
                isProcessing = false;
            }
        }, 'image/jpeg', 0.8);
    }
    
    animationFrameId = requestAnimationFrame(processWebcamFrame);
}

function drawOverlay(data, width, height) {
    console.log('drawOverlay called with:', { data, width, height }); // Debug log
    webcamCanvas.width = width;
    webcamCanvas.height = height;
    webcamCanvas.classList.remove('hidden');
    
    const ctx = webcamCanvas.getContext('2d');
    ctx.clearRect(0, 0, width, height);
    
    if (data.box) {
        console.log('Box found, drawing...'); // Debug log
        const [x, y, w, h] = data.box;
        
        // Draw Cyan Box with rounded corners
        const radius = 15;
        ctx.strokeStyle = '#00FFFF';  // Cyan color
        ctx.lineWidth = 4;  // Thicker line for better visibility
        
        // Draw rounded rectangle at ORIGINAL coordinates
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + w - radius, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
        ctx.lineTo(x + w, y + h - radius);
        ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
        ctx.lineTo(x + radius, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        ctx.stroke();
        
        // Prepare label text
        const labelText = `${data.prediction} ${Math.round(data.confidence * 100)}%`;
        ctx.font = 'bold 18px Inter, sans-serif';
        const textMetrics = ctx.measureText(labelText);
        const textWidth = textMetrics.width;
        const textHeight = 24;
        const padding = 12;
        
        // Draw label at ORIGINAL x coordinate
        const labelY = y - textHeight - padding;
        
        // Draw Label Background
        ctx.fillStyle = 'rgba(0, 255, 255, 0.5)';
        ctx.fillRect(x, labelY, textWidth + padding * 2, textHeight + padding);
        
        // Pre-mirror the text so it appears correct after CSS mirroring
        ctx.save();
        ctx.translate(x + textWidth + padding * 2, labelY);
        ctx.scale(-1, 1);
        
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 18px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText(labelText, padding, 4);
        
        ctx.restore();
    }
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    webcamVideo.srcObject = null;
    webcamCanvas.classList.add('hidden');
    
    webcamSection.classList.add('hidden');
    dropZone.classList.remove('hidden');
}

function captureImage() {
    if (!stream) return;

    // Set canvas dimensions to match video
    webcamCanvas.width = webcamVideo.videoWidth;
    webcamCanvas.height = webcamVideo.videoHeight;
    
    // Draw video frame to canvas
    const ctx = webcamCanvas.getContext('2d');
    ctx.drawImage(webcamVideo, 0, 0, webcamCanvas.width, webcamCanvas.height);
    
    // Convert to blob and upload
    webcamCanvas.toBlob((blob) => {
        if (blob) {
            const file = new File([blob], "webcam-capture.jpg", { type: "image/jpeg" });
            handleFile(file);
            stopWebcam();
        }
    }, 'image/jpeg');
}

async function uploadAndPredict(file) {
    showLoading();
    hideResults();
    hideError();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    if (errorData.error.includes('No face detected')) {
                        errorMessage = "Could not predict emotion, try again using a different image";
                    } else {
                        errorMessage = errorData.error;
                    }
                }
            } catch (e) {
                // Ignore JSON parse error, use default status message
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        hideLoading();
        displayResults(data);
        
    } catch (error) {
        console.error('Prediction error:', error);
        hideLoading();
        showError(error.message || 'Failed to analyze image. Please try again.');
    }
}

// Add this new function to draw box on the preview image
function drawBoxOnPreview(box, emotion, confidence) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = imagePreview;
    
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    
    // Draw the image
    ctx.drawImage(img, 0, 0);
    
    // Draw bounding box
    const [x, y, w, h] = box;
    ctx.strokeStyle = '#00FFFF';  // Cyan
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);
    
    // Draw label
    const label = `${emotion} ${Math.round(confidence * 100)}%`;
    ctx.font = 'bold 16px Inter, sans-serif';
    const textWidth = ctx.measureText(label).width;
    
    // Draw label background
    ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
    ctx.fillRect(x, y - 25, textWidth + 20, 30);
    
    // Draw label text
    ctx.fillStyle = '#00FFFF';
    ctx.fillText(label, x + 10, y - 7);
    
    // Replace preview image with canvas
    imagePreview.src = canvas.toDataURL();
}

function createPredictionItem(prediction, index) {
    const item = document.createElement('div');
    item.className = 'prediction-item';
    
    // Emotion name
    const name = document.createElement('div');
    name.className = 'prediction-name';
    name.textContent = prediction.emotion;
    
    // Progress bar container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    
    // Progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    const percentage = Math.round(prediction.confidence * 100);
    progressBar.style.width = `${percentage}%`;
    
    // Color based on confidence
    if (index === 0) {
        progressBar.style.backgroundColor = '#00FFFF'; // Cyan for top prediction
    } else {
        progressBar.style.backgroundColor = 'rgba(0, 255, 255, 0.3)';
    }
    
    progressContainer.appendChild(progressBar);
    
    // Percentage text
    const percentText = document.createElement('div');
    percentText.className = 'prediction-percent';
    percentText.textContent = `${percentage}%`;
    
    item.appendChild(name);
    item.appendChild(progressContainer);
    item.appendChild(percentText);
    
    return item;
}

function displayResults(data) {
    // Update top prediction
    const topEmotion = data.prediction;
    const topConfidence = Math.round(data.confidence * 100);
    
    emotionIcon.textContent = EMOTION_EMOJIS[topEmotion] || '😊';
    emotionLabel.textContent = topEmotion;
    confidenceValue.textContent = topConfidence;
    
    // Update all predictions list
    predictionsList.innerHTML = '';
    
    data.all_predictions.forEach((pred, index) => {
        const item = createPredictionItem(pred, index);
        predictionsList.appendChild(item);
    });
    
    // Draw bounding box on uploaded image if box data exists
    if (data.box && currentFile) {
        drawBoxOnPreview(data.box, data.prediction, data.confidence);
    }
    
    showResults();
}

async function predictEmotion() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select an image first');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display the image with bounding box
            displayImageWithBox(file, data.box, data.prediction, data.confidence);
        } else {
            alert('Error: ' + (data.error || 'No face detected'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to predict emotion');
    }
}

function displayImageWithBox(file, box, emotion, confidence) {
    const canvas = document.getElementById('resultCanvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        
        // Draw the image
        ctx.drawImage(img, 0, 0);
        
        // Draw bounding box (cyan color to match backend)
        const [x, y, w, h] = box;
        ctx.strokeStyle = '#00FFFF';  // Cyan
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);
        
        // Draw label
        const label = `${emotion} (${(confidence * 100).toFixed(1)}%)`;
        ctx.font = 'bold 16px Arial';
        const textWidth = ctx.measureText(label).width;
        
        // Draw label background
        ctx.fillStyle = '#00FFFF';
        ctx.fillRect(x, y - 25, textWidth + 10, 25);
        
        // Draw label text
        ctx.fillStyle = '#000000';
        ctx.fillText(label, x + 5, y - 7);
    };
    
    img.src = URL.createObjectURL(file);
}

function showLoading() {
    loadingState.classList.remove('hidden');
}

function hideLoading() {
    loadingState.classList.add('hidden');
}

function showResults() {
    resultsSection.classList.remove('hidden');
}

function hideResults() {
    resultsSection.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
}

function hideError() {
    errorState.classList.add('hidden');
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
