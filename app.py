import os
import sys
import subprocess
import threading
import uuid
import json
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Check if running on Render.com
if os.environ.get('RENDER'):
    # Use the persistent disk on Render
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    app.config['UPLOAD_FOLDER'] = os.path.join(data_dir, 'uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(data_dir, 'outputs')
else:
    # Local development paths
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store conversion jobs
conversion_jobs = {}


def check_ffmpeg():
    """Check if FFmpeg is installed and available in the system path"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


@app.route('/')
def index():
    if not check_ffmpeg():
        return render_template('error.html', message="FFmpeg is not installed or not in the system PATH.")
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    # Generate a unique ID for this conversion job
    job_id = str(uuid.uuid4())
    
    # Save the uploaded file
    filename = secure_filename(video_file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    video_file.save(file_path)
    
    # Get conversion parameters
    scale_method = request.form.get('scale_method', 'crop')
    quality = request.form.get('quality', 'medium')
    
    # Create a new conversion job
    conversion_jobs[job_id] = {
        'status': 'queued',
        'progress': 0,
        'input_file': file_path,
        'output_file': None,
        'error': None,
        'start_time': time.time(),
        'original_filename': filename
    }
    
    # Start conversion in a background thread
    thread = threading.Thread(
        target=convert_video,
        args=(job_id, file_path, scale_method, quality)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued'
    })


def convert_video(job_id, input_path, scale_method, quality):
    try:
        # Update job status
        conversion_jobs[job_id]['status'] = 'processing'
        
        # Generate output filename
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        output_filename = f"{job_id}_output{ext}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Set quality parameters
        if quality == "low":
            crf = "28"
        elif quality == "medium":
            crf = "23"
        else:  # high
            crf = "18"
        
        # Build FFmpeg command based on scaling method
        if scale_method == "crop":
            # Crop the sides to fit 9:16 aspect ratio
            cmd = [
                "ffmpeg", "-i", input_path,
                "-vf", "crop=ih*9/16:ih,scale=1080:1920",
                "-c:v", "libx264", "-crf", crf,
                "-c:a", "aac", "-b:a", "128k",
                "-y", output_path
            ]
        else:  # pad with blur
            # Create a blurred, scaled background and overlay the video
            cmd = [
                "ffmpeg", "-i", input_path,
                "-filter_complex", 
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,setsar=1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v];" +
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];" +
                "[bg][v]overlay=(W-w)/2:(H-h)/2",
                "-c:v", "libx264", "-crf", crf,
                "-c:a", "aac", "-b:a", "128k",
                "-y", output_path
            ]
        
        # Run FFmpeg command
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for the process to complete
        stdout, stderr = process.communicate()
        
        # Check if conversion was successful
        if process.returncode == 0:
            conversion_jobs[job_id]['status'] = 'completed'
            conversion_jobs[job_id]['output_file'] = output_path
        else:
            conversion_jobs[job_id]['status'] = 'failed'
            conversion_jobs[job_id]['error'] = stderr
                
    except Exception as e:
        conversion_jobs[job_id]['status'] = 'failed'
        conversion_jobs[job_id]['error'] = str(e)
    
    # Clean up the input file
    try:
        if os.path.exists(input_path):
            # Keep files for debugging in development
            # os.remove(input_path)
            pass
    except:
        pass


@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    
    response = {
        'status': job['status'],
        'progress': job['progress']
    }
    
    if job['status'] == 'completed':
        # Generate download URL
        output_filename = os.path.basename(job['output_file'])
        original_name, ext = os.path.splitext(job['original_filename'])
        download_filename = f"{original_name}_9x16{ext}"
        
        response['download_url'] = url_for('download_file', job_id=job_id, filename=download_filename)
        response['preview_url'] = url_for('preview_file', job_id=job_id)
    
    if job['status'] == 'failed':
        response['error'] = job['error']
    
    return jsonify(response)


@app.route('/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    if job_id not in conversion_jobs or conversion_jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'File not available'}), 404
    
    job = conversion_jobs[job_id]
    output_dir = os.path.dirname(job['output_file'])
    output_filename = os.path.basename(job['output_file'])
    
    return send_from_directory(
        directory=output_dir,
        path=output_filename,
        as_attachment=True,
        download_name=filename
    )


@app.route('/preview/<job_id>', methods=['GET'])
def preview_file(job_id):
    if job_id not in conversion_jobs or conversion_jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'File not available'}), 404
    
    job = conversion_jobs[job_id]
    output_dir = os.path.dirname(job['output_file'])
    output_filename = os.path.basename(job['output_file'])
    
    return send_from_directory(
        directory=output_dir,
        path=output_filename,
        as_attachment=False
    )


@app.route('/cleanup', methods=['POST'])
def cleanup_job():
    job_id = request.json.get('job_id')
    if not job_id or job_id not in conversion_jobs:
        return jsonify({'error': 'Invalid job ID'}), 400
    
    job = conversion_jobs[job_id]
    
    # Remove output file if it exists
    if job['output_file'] and os.path.exists(job['output_file']):
        try:
            os.remove(job['output_file'])
        except:
            pass
    
    # Remove input file if it exists
    if job['input_file'] and os.path.exists(job['input_file']):
        try:
            os.remove(job['input_file'])
        except:
            pass
    
    # Remove job from tracking
    del conversion_jobs[job_id]
    
    return jsonify({'status': 'success'})


# Cleanup old jobs periodically (could be done with a scheduler in production)
def cleanup_old_jobs():
    current_time = time.time()
    jobs_to_remove = []
    
    for job_id, job in conversion_jobs.items():
        # Remove jobs older than 1 hour
        if current_time - job['start_time'] > 3600:  # 1 hour in seconds
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        job = conversion_jobs[job_id]
        
        # Remove files
        if job['output_file'] and os.path.exists(job['output_file']):
            try:
                os.remove(job['output_file'])
            except:
                pass
        
        if job['input_file'] and os.path.exists(job['input_file']):
            try:
                os.remove(job['input_file'])
            except:
                pass
        
        # Remove job from tracking
        del conversion_jobs[job_id]


if __name__ == "__main__":
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in the system PATH.")
        print("Please install FFmpeg and make sure it's available in your PATH.")
        print("Download FFmpeg from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Check if running on Render.com
    if os.environ.get('RENDER'):
        # Production mode
        port = int(os.environ.get('PORT', 10000))
        app.run(debug=False, host='0.0.0.0', port=port)
    else:
        # Development mode
        app.run(debug=True, host='0.0.0.0', port=5000)