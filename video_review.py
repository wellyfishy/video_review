import sys
import cv2
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QComboBox, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

class WebcamRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webcam Recorder")
        self.setGeometry(200, 200, 800, 600)

        self.captures = []
        self.recording = False
        self.outs = []
        self.timer = QTimer()

        # Camera selection dropdowns
        self.cam1_select = QComboBox()
        self.cam2_select = QComboBox()
        for i in range(5):  # Check first 5 indices
            self.cam1_select.addItem(f"Camera {i}")
            self.cam2_select.addItem(f"Camera {i}")

        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)

        # Buttons
        self.start_btn = QPushButton("Start Recording")
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.setEnabled(False)

        # Layout
        layout = QVBoxLayout()
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(self.cam1_select)
        cam_layout.addWidget(self.cam2_select)
        layout.addLayout(cam_layout)
        layout.addWidget(self.preview_label)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Connections
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.timer.timeout.connect(self.update_preview)

    def start_recording(self):
        # Open cameras
        cam1_index = self.cam1_select.currentIndex()
        cam2_index = self.cam2_select.currentIndex()

        self.captures = []
        self.outs = []

        # Open first camera
        cap1 = cv2.VideoCapture(cam1_index)
        if cap1.isOpened():
            self.captures.append(cap1)
            self.outs.append(self.create_writer(cap1, f"camera1_{self.timestamp()}.avi"))

        # Open second camera (only if different index)
        if cam2_index != cam1_index:
            cap2 = cv2.VideoCapture(cam2_index)
            if cap2.isOpened():
                self.captures.append(cap2)
                self.outs.append(self.create_writer(cap2, f"camera2_{self.timestamp()}.avi"))

        if not self.captures:
            print("No camera opened!")
            return

        self.recording = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.timer.start(30)  # 30ms interval (~33 FPS)

    def stop_recording(self):
        self.recording = False
        self.timer.stop()

        for cap in self.captures:
            cap.release()
        for out in self.outs:
            out.release()

        self.captures = []
        self.outs = []
        self.preview_label.clear()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("Recording stopped.")

    def update_preview(self):
        if not self.captures:
            return

        frames = []
        for i, cap in enumerate(self.captures):
            ret, frame = cap.read()
            if not ret:
                continue

            if self.recording:
                self.outs[i].write(frame)

            frames.append(frame)

        if frames:
            # If two cameras, show side-by-side preview
            if len(frames) == 2:
                frame = cv2.hconcat(frames)
            else:
                frame = frames[0]

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.preview_label.setPixmap(QPixmap.fromImage(q_img))

    def create_writer(self, cap, filename):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return cv2.VideoWriter(filename, fourcc, fps, (width, height))

    def timestamp(self):
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebcamRecorder()
    window.show()
    sys.exit(app.exec_())
