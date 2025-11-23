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

// State
let currentFile = null;

// Initialize
function init() {
    setupEventListeners();
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
            throw new Error(`Server error: ${response.status}`);
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
    
    showResults();
}

function createPredictionItem(prediction, index) {
    const item = document.createElement('div');
    item.className = 'prediction-item';
    item.style.animationDelay = `${index * 0.05}s`;
    
    const emoji = document.createElement('div');
    emoji.className = 'prediction-emoji';
    emoji.textContent = EMOTION_EMOJIS[prediction.emotion] || '😊';
    
    const info = document.createElement('div');
    info.className = 'prediction-info';
    
    const name = document.createElement('div');
    name.className = 'prediction-name';
    name.textContent = prediction.emotion;
    
    const barContainer = document.createElement('div');
    barContainer.className = 'prediction-bar-container';
    
    const bar = document.createElement('div');
    bar.className = 'prediction-bar';
    const percentage = prediction.confidence * 100;
    
    // Animate bar width
    setTimeout(() => {
        bar.style.width = `${percentage}%`;
    }, 100 + index * 50);
    
    barContainer.appendChild(bar);
    
    info.appendChild(name);
    info.appendChild(barContainer);
    
    const percentageText = document.createElement('div');
    percentageText.className = 'prediction-percentage';
    percentageText.textContent = `${Math.round(percentage)}%`;
    
    item.appendChild(emoji);
    item.appendChild(info);
    item.appendChild(percentageText);
    
    return item;
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
