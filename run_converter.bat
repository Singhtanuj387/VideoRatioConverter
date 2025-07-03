@echo off
echo Installing required packages...
pip install -r requirements.txt

echo Starting Video Ratio Converter Web App...
echo.
echo Once the server is running, open your browser and go to: http://localhost:5000
echo.
python app.py
pause