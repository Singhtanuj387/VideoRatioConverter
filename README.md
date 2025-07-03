# Video Ratio Converter (16:9 to 9:16)

A web application that converts videos from 16:9 (landscape) ratio to 9:16 (portrait) ratio, perfect for adapting content for platforms like TikTok, Instagram Reels, and YouTube Shorts.

**Live Demo:** [https://videoratioconverter.onrender.com/](https://videoratioconverter.onrender.com/)

## Features

- Convert videos from landscape (16:9) to portrait (9:16) format
- Two conversion methods:
  - **Crop**: Crops the sides of the video to fit the 9:16 ratio
  - **Pad with blur**: Keeps the full video and adds a blurred background
- Adjustable quality settings (low, medium, high)
- Modern, responsive web interface
- Progress tracking during conversion
- Video preview after conversion
- Easy download of converted videos

## Requirements

- Python 3.6 or higher
- FFmpeg (must be installed and available in your system PATH)
- Python packages (automatically installed by the setup script):
  - Flask
  - Werkzeug
  - Gunicorn (for production deployment)

## Installation

1. Make sure you have Python installed on your system
2. Install FFmpeg:
   - **Windows**: Download from [FFmpeg.org](https://ffmpeg.org/download.html) and add to your PATH
   - **macOS**: Install using Homebrew: `brew install ffmpeg`
   - **Linux**: Install using your package manager, e.g., `sudo apt install ffmpeg`
3. Clone or download this repository

## Usage

### Windows

1. Double-click the `run_converter.bat` file
2. The script will install required packages and start the web server
3. Open your browser and go to: http://localhost:5000

### Manual Start (All Platforms)

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Open your browser and go to: http://localhost:5000

## How to Use

1. Upload your video using the file upload area (drag & drop or browse)
2. Select your preferred conversion method:
   - **Crop**: Will crop the sides of the video to fit 9:16 ratio
   - **Pad with blur**: Will keep the entire video and add a blurred background
3. Choose your desired output quality
4. Click "Convert Video" to start the conversion process
5. Wait for the conversion to complete
6. Preview the converted video in your browser
7. Download the converted video

## How It Works

The application uses FFmpeg to process the video with the following approaches:

### Crop Method
Crops the sides of the video to focus on the center portion, then scales it to fit the 9:16 ratio (typically 1080x1920 pixels).

### Pad with Blur Method
Keeps the entire original video and adds a blurred, zoomed version of the video as the background to fill the 9:16 frame.

## Troubleshooting

- **FFmpeg not found**: Ensure FFmpeg is properly installed and added to your system PATH
- **Conversion fails**: Check that you have write permissions to the application directories
- **Upload issues**: Make sure your video file is less than 500MB and in a supported format
  
### Manual Deployment

For manual deployment, consider using Gunicorn or uWSGI with a reverse proxy like Nginx:

```
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

## License

This project is open source and available under the MIT License.
