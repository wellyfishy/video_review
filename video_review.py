import tkinter as tk
from tkinter import ttk
import subprocess, cv2, re, datetime
from PIL import Image, ImageTk

process = None
cap1, cap2 = None, None

# 🔹 Detect cameras using FFmpeg
def get_cameras():
    result = subprocess.run(
        ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
        stderr=subprocess.PIPE, text=True
    )
    return re.findall(r'"([^"]+)" \(video\)', result.stderr)

# 🔹 Start preview with OpenCV
def start_preview():
    global cap1, cap2
    idx1 = cam1_menu.current()
    idx2 = cam2_menu.current()

    if idx1 >= 0:
        cap1 = cv2.VideoCapture(idx1, cv2.CAP_DSHOW)
    if idx2 >= 0:
        cap2 = cv2.VideoCapture(idx2, cv2.CAP_DSHOW)

    update_frames()

def update_frames():
    global cap1, cap2
    if cap1:
        ret, frame = cap1.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            preview1.config(image=img)
            preview1.image = img

    if cap2:
        ret, frame = cap2.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            preview2.config(image=img)
            preview2.image = img

    root.after(30, update_frames)

# 🔹 Start recording with FFmpeg
def start_recording():
    global process
    cam1 = cam1_var.get()
    cam2 = cam2_var.get()

    if not cam1 and not cam2:
        status_label.config(text="⚠ Please select at least 1 camera!", fg="red")
        return

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ffmpeg_cmd = ["ffmpeg", "-y"]

    if cam1:
        ffmpeg_cmd += ["-f", "dshow", "-i", f"video={cam1}"]
    if cam2:
        ffmpeg_cmd += ["-f", "dshow", "-i", f"video={cam2}"]

    # Output for camera 1
    if cam1:
        ffmpeg_cmd += [
            "-map", "0:v",
            "-c:v", "libx264", "-profile:v", "baseline", "-pix_fmt", "yuv420p",
            "-b:v", "5M", "-r", "30", "-s", "1280x720", f"cam1_{ts}.mp4"
        ]

    # Output for camera 2
    if cam2:
        idx = 0 if not cam1 else 1
        ffmpeg_cmd += [
            "-map", f"{idx}:v",
            "-c:v", "libx264", "-profile:v", "baseline", "-pix_fmt", "yuv420p",
            "-b:v", "5M", "-r", "30", "-s", "1280x720", f"cam2_{ts}.mp4"
        ]

    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    status_label.config(text="Recording...", fg="green")

# 🔹 Stop recording properly
def stop_recording():
    global process
    if process:
        try:
            process.stdin.write(b"q")
            process.stdin.flush()
            process.wait()
        except:
            process.terminate()
        process = None
        status_label.config(text="Stopped", fg="red")

# 🔹 GUI Setup
root = tk.Tk()
root.title("Dual Webcam Recorder")

cam1_var, cam2_var = tk.StringVar(), tk.StringVar()

tk.Label(root, text="Camera 1").pack()
cam1_menu = ttk.Combobox(root, textvariable=cam1_var, state="readonly")
cam1_menu.pack()

tk.Label(root, text="Camera 2").pack()
cam2_menu = ttk.Combobox(root, textvariable=cam2_var, state="readonly")
cam2_menu.pack()

def refresh_cameras():
    cams = get_cameras()
    cam1_menu["values"] = cams
    cam2_menu["values"] = cams

tk.Button(root, text="Refresh Cameras", command=refresh_cameras).pack(pady=5)
tk.Button(root, text="Start Preview", command=start_preview).pack(pady=5)

preview_frame = tk.Frame(root)
preview_frame.pack(pady=10)

preview1 = tk.Label(preview_frame)
preview1.pack(side="left", padx=5)

preview2 = tk.Label(preview_frame)
preview2.pack(side="left", padx=5)

tk.Button(root, text="Start Recording", command=start_recording).pack(pady=5)
tk.Button(root, text="Stop Recording", command=stop_recording).pack(pady=5)

status_label = tk.Label(root, text="Idle", fg="gray")
status_label.pack(pady=5)

refresh_cameras()
root.mainloop()
