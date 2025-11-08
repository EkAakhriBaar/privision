import subprocess
import numpy as np
import mss

# === USER SETTINGS ===
# Choose your streaming platform
PLATFORM = "youtube"  # Options: "youtube", "facebook", "twitch"

# Platform RTMP URLs
RTMP_URLS = {
    "youtube": "rtmp://a.rtmp.youtube.com/live2/",
    "facebook": "rtmps://live-api-s.facebook.com:443/rtmp/",
    "twitch": "rtmp://live.twitch.tv/app/"
}

RTMP_URL = RTMP_URLS[PLATFORM]
STREAM_KEY = "YOUR_STREAM_KEY_HERE"  # Replace with your actual stream key

# === SCREEN SETTINGS ===
sct = mss.mss()
monitor = sct.monitors[1]
width = monitor["width"]
height = monitor["height"]
fps = 30

# === BASE FFMPEG COMMAND ===
ffmpeg_cmd = [
    "ffmpeg",
    "-loglevel", "verbose",
    "-y",

    # Input 0: raw video from stdin
    "-thread_queue_size", "512",       # 🟢 Must be before the corresponding -i
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{width}x{height}",
    "-r", str(fps),
    "-i", "-",                         # stdin video stream

    # Input 1: silent audio
    "-thread_queue_size", "512",       # 🟢 for lavfi input as well
    "-f", "lavfi", "-i", "anullsrc",

    # Output encoding
    "-vf", "scale=1280:720",           # downscale to 720p for smoother streaming
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "veryfast",
    "-b:v", "4500k",
    "-g", str(fps * 2),
    "-c:a", "aac",
    "-ar", "44100",
    "-b:a", "128k",
    "-f", "flv",
    f"{RTMP_URL}{STREAM_KEY}"
]

# === START FFMPEG PROCESS ===
process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

print("🚀 Streaming started... Press Ctrl+C to stop.")

try:
    while True:
        img = np.array(sct.grab(monitor))
        frame = img[..., :3]
        process.stdin.write(frame.tobytes())
except KeyboardInterrupt:
    print("\n🛑 Streaming stopped.")
    process.stdin.close()
    process.wait()