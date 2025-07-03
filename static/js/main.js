// Main JavaScript for Video Ratio Converter

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const uploadArea = document.getElementById('upload-area');
    const videoFileInput = document.getElementById('video-file');
    const fileInfo = document.getElementById('file-info');
    const filename = document.getElementById('filename');
    const removeFileBtn = document.getElementById('remove-file');
    const convertBtn = document.getElementById('convert-btn');
    
    // State containers
    const initialState = document.getElementById('initial-state');
    const processingState = document.getElementById('processing-state');
    const completedState = document.getElementById('completed-state');
    const errorState = document.getElementById('error-state');
    
    // Progress elements
    const progressBar = document.getElementById('progress-bar');
    const statusMessage = document.getElementById('status-message');
    
    // Result elements
    const previewVideo = document.getElementById('preview-video');
    const previewSource = document.getElementById('preview-source');
    const downloadLink = document.getElementById('download-link');
    const errorMessage = document.getElementById('error-message');
    
    // Action buttons
    const convertAnotherBtn = document.getElementById('convert-another');
    const tryAgainBtn = document.getElementById('try-again');
    
    // Current job ID
    let currentJobId = null;
    let statusCheckInterval = null;
    
    // File Upload Handling
    videoFileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            videoFileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });
    
    uploadArea.addEventListener('click', function() {
        videoFileInput.click();
    });
    
    // Remove file button
    removeFileBtn.addEventListener('click', function() {
        resetFileUpload();
    });
    
    // Form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        startConversion();
    });
    
    // Convert another button
    convertAnotherBtn.addEventListener('click', function() {
        resetAll();
    });
    
    // Try again button
    tryAgainBtn.addEventListener('click', function() {
        resetAll();
    });
    
    // File selection handler
    function handleFileSelect() {
        if (videoFileInput.files.length > 0) {
            const file = videoFileInput.files[0];
            
            // Check if it's a video file
            if (!file.type.startsWith('video/')) {
                alert('Please select a valid video file.');
                resetFileUpload();
                return;
            }
            
            // Check file size (max 500MB)
            if (file.size > 500 * 1024 * 1024) {
                alert('File size exceeds the 500MB limit.');
                resetFileUpload();
                return;
            }
            
            // Display file info
            filename.textContent = file.name;
            fileInfo.classList.remove('d-none');
            uploadArea.classList.add('d-none');
            convertBtn.disabled = false;
        }
    }
    
    // Reset file upload
    function resetFileUpload() {
        videoFileInput.value = '';
        fileInfo.classList.add('d-none');
        uploadArea.classList.remove('d-none');
        convertBtn.disabled = true;
    }
    
    // Start conversion process
    function startConversion() {
        if (!videoFileInput.files.length) {
            return;
        }
        
        // Show processing state
        showState('processing');
        
        // Create form data
        const formData = new FormData(uploadForm);
        
        // Send the file to the server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store the job ID
            currentJobId = data.job_id;
            
            // Start checking status
            statusCheckInterval = setInterval(checkConversionStatus, 2000);
        })
        .catch(error => {
            showError('Upload failed: ' + error.message);
        });
    }
    
    // Check conversion status
    function checkConversionStatus() {
        if (!currentJobId) {
            clearInterval(statusCheckInterval);
            return;
        }
        
        fetch(`/status/${currentJobId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update progress
            updateProgress(data.status, data.progress);
            
            // Check if completed
            if (data.status === 'completed') {
                clearInterval(statusCheckInterval);
                conversionCompleted(data.download_url, data.preview_url);
            }
            
            // Check if failed
            if (data.status === 'failed') {
                clearInterval(statusCheckInterval);
                showError(data.error || 'Conversion failed');
            }
        })
        .catch(error => {
            clearInterval(statusCheckInterval);
            showError('Status check failed: ' + error.message);
        });
    }
    
    // Update progress UI
    function updateProgress(status, progress) {
        // Update progress bar (if progress is available)
        if (typeof progress === 'number') {
            progressBar.style.width = `${progress}%`;
        } else {
            // If no progress info, just animate the bar
            progressBar.style.width = '100%';
        }
        
        // Update status message
        if (status === 'queued') {
            statusMessage.textContent = 'Waiting in queue...';
        } else if (status === 'processing') {
            statusMessage.textContent = 'Converting your video... This may take a few minutes.';
        }
    }
    
    // Handle conversion completion
    function conversionCompleted(downloadUrl, previewUrl) {
        // Set download link
        downloadLink.href = downloadUrl;
        
        // Set preview video source
        previewSource.src = previewUrl;
        previewVideo.load();
        
        // Show completed state
        showState('completed');
        
        // Clean up after a while
        setTimeout(() => {
            if (currentJobId) {
                fetch('/cleanup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ job_id: currentJobId })
                }).catch(() => {});
            }
        }, 300000); // Clean up after 5 minutes
    }
    
    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        showState('error');
    }
    
    // Show specific state and hide others
    function showState(state) {
        // Hide all states
        initialState.classList.add('d-none');
        processingState.classList.add('d-none');
        completedState.classList.add('d-none');
        errorState.classList.add('d-none');
        
        // Show requested state
        if (state === 'initial') {
            initialState.classList.remove('d-none');
        } else if (state === 'processing') {
            processingState.classList.remove('d-none');
        } else if (state === 'completed') {
            completedState.classList.remove('d-none');
        } else if (state === 'error') {
            errorState.classList.remove('d-none');
        }
    }
    
    // Reset everything
    function resetAll() {
        // Clear intervals
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
        }
        
        // Reset file upload
        resetFileUpload();
        
        // Reset progress
        progressBar.style.width = '0%';
        
        // Reset video preview
        previewSource.src = '';
        previewVideo.load();
        
        // Show initial state
        showState('initial');
        
        // Clear job ID
        currentJobId = null;
    }
});