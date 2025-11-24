"""
Simple camera test to check brightness values
"""
import cv2
import numpy as np
import time

print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Failed to open camera")
    exit(1)

print("Camera opened successfully")

# Set properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Waiting 2 seconds for camera to initialize...")
time.sleep(2)

print("\nReading 30 frames and checking brightness:")
for i in range(30):
    ret, frame = cap.read()
    if ret and frame is not None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        min_val = np.min(gray)
        max_val = np.max(gray)
        print(f"Frame {i+1}: brightness={brightness:.2f}, min={min_val}, max={max_val}")
    else:
        print(f"Frame {i+1}: Failed to read")

cap.release()
print("\nTest complete!")
