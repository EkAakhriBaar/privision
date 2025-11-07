# Quick Start Guide

## Installation (First Time)

### Step 1: Install Python
- Download Python 3.8+ from python.org
- Make sure to check "Add Python to PATH" during installation

### Step 2: Install Dependencies
```bash
cd d:\Desktop\screenshare
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python src/screen_recorder.py
```

## Basic Recording

### Scenario 1: Simple Screen Recording
```
1. Run the application
2. Click "▶ START SHARING" (green button)
3. Screen recording starts
4. Your activity is captured
5. Click "⏹ STOP SHARING" (red button) when done
6. Video saved to recordings/recording_YYYYMMDD_HHMMSS.mp4
```

### Scenario 2: Record with Custom Resolution
```
1. Before clicking START:
   - Select resolution from dropdown (e.g., "1280x720")
2. Optionally adjust FPS (e.g., 24 for smoother)
3. Click "▶ START SHARING"
4. Do your recording
5. Click "⏹ STOP SHARING"
```

### Scenario 3: Record with Face Blur
```
1. ✅ Check "🔒 Blur Faces" checkbox
2. Click "▶ START SHARING"
3. Live preview shows faces being blurred
4. Record your screen
5. Click "⏹ STOP SHARING"
6. Video includes blurred faces
```

## Finding Your Recordings

### Location
```
d:\Desktop\screenshare\recordings\
```

### File Format
```
recording_20251107_145230.mp4
recording_20251107_150100.mp4
recording_20251107_160530.mp4
```

### Opening Videos
- Double-click to play in default media player
- Right-click → "Open with" to choose specific player
- Use VLC Media Player for best compatibility

## Common Tasks

### Task: Record a Presentation
1. Open presentation (PowerPoint, Google Slides, etc.)
2. Run Screen Recorder
3. Select 1920x1080 resolution
4. Set FPS to 30
5. Click START
6. Present normally
7. Click STOP when done

### Task: Record a Tutorial
1. Run Screen Recorder
2. Check "Blur Faces" if you want privacy
3. Select 1280x720 (good balance)
4. Set FPS to 30
5. Click START
6. Do your tutorial
7. Click STOP

### Task: Record Meeting with Privacy
1. Check "🔒 Blur Faces" box
2. Click START
3. All faces in video will be blurred
4. Click STOP
5. Video is ready to share safely

### Task: Change Quality Settings
```
For faster/smaller files:
- Resolution: 1280x720
- FPS: 24

For better quality:
- Resolution: 1920x1080
- FPS: 30-45

For maximum quality:
- Resolution: 1920x1080
- FPS: 60
```

## Tips & Tricks

### Tip 1: Preview Before Recording
- Live preview shows what will be recorded
- Check preview to ensure screen is visible
- Adjust settings based on preview quality

### Tip 2: Monitor Available Space
```
File sizes (approximate):
- 5 minutes @ 1920x1080 30FPS = ~500MB
- 10 minutes @ 1920x1080 30FPS = ~1GB
- 1 minute @ 1280x720 30FPS = ~50MB
```

### Tip 3: Close Unnecessary Apps
- Close background applications for better performance
- Reduces CPU usage
- Smoother recording without lag
- Better FPS stability

### Tip 4: Use Optimal Settings
```
Balanced (recommended):
- Resolution: 1920x1080 or 1280x720
- FPS: 30
- Face Blur: Optional

Performance Mode:
- Resolution: 1024x768
- FPS: 24
- Face Blur: OFF

Quality Mode:
- Resolution: 1920x1080
- FPS: 60
- Face Blur: OFF
```

### Tip 5: Audio Capture
- Application captures video only
- Record audio separately using:
  - Audacity (free audio recorder)
  - OBS Studio (free, records video + audio)
  - Your phone's voice memo app

## Troubleshooting

### Issue: Application Won't Start
```
Solution:
1. Open Terminal/PowerShell
2. cd d:\Desktop\screenshare
3. python src/screen_recorder.py
4. Check error messages in terminal
5. Install any missing packages: pip install PyQt5 opencv-python numpy mss
```

### Issue: Recording is Slow
```
Solution:
1. Close other applications
2. Lower resolution (try 1280x720)
3. Lower FPS (try 24 instead of 30)
4. Disable face blur
5. Check available disk space
```

### Issue: Faces Not Blurring
```
Solution:
1. Ensure "Blur Faces" checkbox is checked
2. Make sure faces are clearly visible
3. Check lighting (need good light)
4. Ensure face is at least 24x24 pixels
5. Try getting closer to camera
```

### Issue: No Sound in Recording
```
Note: Application records VIDEO only
Solution: Use OBS Studio or audacity for combined audio+video
or record audio separately and sync later
```

### Issue: Recording Not Saving
```
Solution:
1. Check if recordings/ folder exists
2. Verify write permissions on folder
3. Check available disk space
4. Check error message in status bar
5. Try saving to different location
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Alt+F4 | Close application (stops recording if active) |
| Click START | Begin recording |
| Click STOP | End recording |

## File Management

### View Recent Recordings
```
File Explorer → d:\Desktop\screenshare\recordings\
```

### Delete Old Recordings
```
1. Open recordings folder
2. Right-click file → Delete
3. Or select multiple files → Delete
```

### Move Recordings to Cloud
```
1. Open recordings folder
2. Select files → Copy
3. Paste to Google Drive / OneDrive / Dropbox
4. Or right-click → Send to → Compressed folder
```

### Compress Videos
```
Using VLC Media Player:
1. Open VLC
2. Media → Convert/Save
3. Select video file
4. Choose codec (H.264 default)
5. Set quality
6. Convert
```

## Advanced Usage

### Custom Resolution
Edit `src/screen_recorder.py`:
```python
self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768", "800x600", "2560x1440"])
```

### Custom FPS Range
Edit `src/screen_recorder.py`:
```python
# Change from:
self.fps_spinbox.setRange(10, 60)
# To:
self.fps_spinbox.setRange(10, 120)  # Support 120 FPS
```

### Adjust Blur Intensity
Edit `src/screen_recorder.py`:
```python
# Stronger blur:
self.BLUR_SIGMA = 50
self.BLUR_KSIZE = (71, 71)

# Lighter blur:
self.BLUR_SIGMA = 15
self.BLUR_KSIZE = (31, 31)
```

## System Requirements

### Minimum
- Windows 7 / macOS 10.12 / Ubuntu 16.04
- Python 3.7+
- 2GB RAM
- 5GB free disk space

### Recommended
- Windows 10/11 / macOS 11+ / Ubuntu 20.04
- Python 3.9+
- 8GB RAM
- 50GB free disk space
- SSD (for better performance)

### Optimal
- Windows 11 / macOS 13+ / Ubuntu 22.04
- Python 3.11+
- 16GB RAM
- 100GB+ free disk space on SSD
- Multi-core CPU (4+ cores)

## Next Steps

1. **Basic Recording**
   - [ ] Run application
   - [ ] Click START
   - [ ] Record 10 seconds
   - [ ] Click STOP
   - [ ] Find video in recordings/ folder

2. **Privacy Recording**
   - [ ] Check "Blur Faces"
   - [ ] Click START
   - [ ] Watch live preview
   - [ ] Record 30 seconds
   - [ ] Click STOP
   - [ ] Play video to verify blur

3. **Advanced**
   - [ ] Try different resolutions
   - [ ] Experiment with FPS settings
   - [ ] Use face blur feature
   - [ ] Upload to cloud
   - [ ] Share recordings

## Support

- **Documentation**: See README.md
- **Face Blur Guide**: See FACE_BLUR_FEATURE.md
- **Errors**: Check terminal output
- **Issues**: Verify all dependencies installed

---

**Ready to start? Run: `python src/screen_recorder.py`** 🎬
