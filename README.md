# Screen Sharing Application

A professional desktop screen recording and sharing application built with PyQt5. Record your screen with customizable resolution and FPS, with intuitive UI/UX design and advanced privacy features like automatic face blurring.

## Features

- 🎥 **Screen Recording**: Record your entire screen with high quality
- 🎮 **Customizable Resolution**: Choose from multiple resolution options (1920x1080, 1280x720, 1024x768, 800x600)
- ⚙️ **Adjustable FPS**: Set recording frame rate from 10 to 60 FPS
- 📊 **Real-time Statistics**: Frame counter and elapsed time display
- 💾 **Auto-save**: Recordings automatically saved with timestamp
- 🎨 **Modern UI/UX**: Professional dark theme with gradient buttons and intuitive controls
- 🔒 **Face Blur Privacy**: Automatic face detection and blurring to protect privacy
- 👁️ **Live Preview**: See what's being recorded before saving with face blur applied

## New Features - Face Blur

### Privacy Protection
The application includes an advanced face detection and blurring feature powered by:
- **Haar Cascade Classifier**: OpenCV's robust face detection algorithm
- **Gaussian Blur**: High-quality blur effect (51x51 kernel, sigma 30)
- **Real-time Processing**: Efficient detection every 2 frames for performance

### How to Use Face Blur
1. **Enable Face Blur**: Check the "🔒 Blur Faces" checkbox before or during recording
2. **Live Preview**: See faces being blurred in real-time in the preview window
3. **Saved Videos**: All blurred faces are recorded in the output video
4. **Toggle Anytime**: Enable/disable during recording session

### Face Blur Configuration
- **Detection Interval**: Every 2nd frame (optimized for performance)
- **Blur Kernel**: 51x51 pixels
- **Blur Strength**: Sigma 30 (high privacy)
- **Performance**: Minimal impact on recording quality and speed

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python src/screen_recorder.py
```

### Controls

- **START SHARING**: Begin recording your screen
- **STOP SHARING**: Stop the current recording
- **Resolution Selector**: Choose recording resolution before starting
- **FPS Spinbox**: Adjust frames per second (10-60)
- **🔒 Blur Faces**: Toggle automatic face blurring on/off

### Recording Storage

All recordings are saved to the `recordings/` directory with timestamp filenames:
- Format: `recording_YYYYMMDD_HHMMSS.mp4`
- Includes: All applied effects (face blur if enabled)

## System Requirements

- Python 3.7 or higher
- Windows, macOS, or Linux
- 2GB RAM minimum
- Available storage space for video files

## Keyboard Shortcuts

- **Alt+F4**: Close the application (will stop recording if active)
- **ESC**: Can be configured to exit preview/recording

## Video Output

- **Format**: MP4 (H.264 codec)
- **Quality**: Depends on selected resolution and FPS
- **Effects**: Face blur applied in real-time during recording
- **Location**: `recordings/` folder in the application directory

## Troubleshooting

### Application crashes on start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.7+)

### Recording not saving
- Verify write permissions in the `recordings/` directory
- Check available disk space
- Ensure the directory exists (it's created automatically)

### Low frame rate
- Close other resource-intensive applications
- Reduce resolution or FPS settings
- Disable face blur to reduce CPU usage
- Check CPU usage

### Face blur not working
- Ensure OpenCV (cv2) is properly installed
- Check that your face is clearly visible to the camera
- Ensure adequate lighting for face detection

### Video quality issues
- Increase FPS for smoother playback
- Use higher resolution for better clarity
- Ensure system has sufficient performance
- Disable face blur if performance is critical

### Face blur too blurry/not blurry enough
- The current blur settings are optimized for privacy
- Settings are in the code: `BLUR_KSIZE`, `BLUR_SIGMA`
- Modify these values in `src/screen_recorder.py` to adjust blur level

## Performance Tips

- Use 30 FPS for standard recording
- Choose 1280x720 or 1920x1080 for best balance
- Close unnecessary applications before recording
- Ensure sufficient free disk space (10GB recommended for long sessions)
- Face blur adds minimal overhead (detects every 2 frames)

## Advanced Configuration

You can customize the face blur behavior by editing `src/screen_recorder.py`:

```python
# Line numbers in __init__ method:
self.BLUR_KSIZE = (51, 51)      # Blur kernel size (larger = more blur)
self.BLUR_SIGMA = 30            # Blur sigma (larger = more blur)
self.DETECT_EVERY = 2           # Detect faces every Nth frame (lower = more CPU usage)
self.MONITOR_INDEX = 1          # Monitor to record (1 = primary)
```

## License

This project is provided as-is for personal and professional use.

## Support

For issues or feature requests, please refer to the documentation or contact the development team.

## Technical Stack

- **PyQt5**: Professional GUI framework
- **OpenCV (cv2)**: Video recording and face detection
- **NumPy**: Array and numerical operations
- **MSS**: Fast screen capture
- **Pillow**: Image processing

---

**Enjoy your professional screen recording application with privacy protection!** 🎬🔒

