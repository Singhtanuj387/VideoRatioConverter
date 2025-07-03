import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

class VideoRatioConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Ratio Converter (16:9 to 9:16)")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Set style
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Video Ratio Converter", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(main_frame, text="Convert videos from 16:9 (landscape) to 9:16 (portrait) ratio")
        desc_label.pack(pady=5)
        
        # Input file section
        input_frame = ttk.LabelFrame(main_frame, text="Input Video", padding="10")
        input_frame.pack(fill=tk.X, pady=10)
        
        self.input_path_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var, width=50)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(input_frame, text="Browse", command=self.browse_input)
        browse_btn.pack(side=tk.RIGHT)
        
        # Output directory section
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.pack(fill=tk.X, pady=10)
        
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_frame, text="Browse", command=self.browse_output)
        browse_output_btn.pack(side=tk.RIGHT)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Conversion Options", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Scaling method
        scale_frame = ttk.Frame(options_frame)
        scale_frame.pack(fill=tk.X, pady=5)
        
        scale_label = ttk.Label(scale_frame, text="Scaling Method:")
        scale_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.scale_method = tk.StringVar(value="crop")
        crop_radio = ttk.Radiobutton(scale_frame, text="Crop", variable=self.scale_method, value="crop")
        crop_radio.pack(side=tk.LEFT, padx=5)
        
        pad_radio = ttk.Radiobutton(scale_frame, text="Pad (with blur)", variable=self.scale_method, value="pad")
        pad_radio.pack(side=tk.LEFT, padx=5)
        
        # Quality setting
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        
        quality_label = ttk.Label(quality_frame, text="Output Quality:")
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_var = tk.StringVar(value="medium")
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, 
                                    values=["low", "medium", "high"], state="readonly", width=10)
        quality_combo.pack(side=tk.LEFT)
        
        # Convert button and progress bar
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        convert_btn = ttk.Button(control_frame, text="Convert", command=self.start_conversion)
        convert_btn.pack(side=tk.RIGHT, padx=5)
        
    def browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Input Video", filetypes=filetypes)
        if filename:
            self.input_path_var.set(filename)
            # Auto-set output directory to same as input
            if not self.output_path_var.get():
                self.output_path_var.set(os.path.dirname(filename))
    
    def browse_output(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path_var.set(directory)
    
    def start_conversion(self):
        input_path = self.input_path_var.get()
        output_dir = self.output_path_var.get()
        
        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid input video file")
            return
        
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output directory")
            return
        
        # Start conversion in a separate thread
        self.progress.start()
        self.status_var.set("Converting...")
        
        conversion_thread = threading.Thread(
            target=self.convert_video,
            args=(input_path, output_dir, self.scale_method.get(), self.quality_var.get())
        )
        conversion_thread.daemon = True
        conversion_thread.start()
    
    def convert_video(self, input_path, output_dir, scale_method, quality):
        try:
            # Generate output filename
            input_filename = os.path.basename(input_path)
            name, ext = os.path.splitext(input_filename)
            output_filename = f"{name}_9x16{ext}"
            output_path = os.path.join(output_dir, output_filename)
            
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
                self.root.after(0, self.conversion_complete, output_path)
            else:
                self.root.after(0, self.conversion_failed, stderr)
                
        except Exception as e:
            self.root.after(0, self.conversion_failed, str(e))
    
    def conversion_complete(self, output_path):
        self.progress.stop()
        self.status_var.set("Conversion complete!")
        messagebox.showinfo("Success", f"Video converted successfully!\n\nOutput saved to:\n{output_path}")
    
    def conversion_failed(self, error_message):
        self.progress.stop()
        self.status_var.set("Conversion failed")
        messagebox.showerror("Error", f"Failed to convert video:\n\n{error_message}")


def check_ffmpeg():
    """Check if FFmpeg is installed and available in the system path"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def main():
    # Check for FFmpeg
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in the system PATH.")
        print("Please install FFmpeg and make sure it's available in your PATH.")
        print("Download FFmpeg from: https://ffmpeg.org/download.html")
        
        # Show error in GUI if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required but not found on your system.\n\n"
                "Please install FFmpeg and make sure it's available in your PATH.\n"
                "Download FFmpeg from: https://ffmpeg.org/download.html"
            )
            root.destroy()
        except:
            pass
        
        sys.exit(1)
    
    # Start the GUI
    root = tk.Tk()
    app = VideoRatioConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()