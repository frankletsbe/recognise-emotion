"""
Improved camera viewer with better initialization
"""
import cv2
import numpy as np
import time

print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Failed to open camera")
    exit(1)

print("Camera opened!")

# Set basic properties BEFORE reading frames
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# CRITICAL: Wait for camera to initialize
print("Waiting for camera to initialize...")
time.sleep(2)

# CRITICAL: Discard first 15 frames (often black)
print("Discarding first 15 frames...")
for i in range(15):
    cap.read()
    time.sleep(0.05)

print("Starting camera feed... Press 'q' to quit\n")

frame_count = 0
good_frames = 0
black_frames = 0

while True:
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("Failed to read frame")
        break
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate stats
    brightness = np.mean(gray)
    max_val = np.max(gray)
    
    # Track black frames
    if brightness < 5:
        black_frames += 1
        print(f"WARNING: Black frame detected! (brightness={brightness:.2f})")
    else:
        good_frames += 1
    
    # Enhance contrast for better visibility
    enhanced = cv2.equalizeHist(gray)
    enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    # Add text overlay
    status_color = (0, 255, 0) if brightness > 10 else (0, 0, 255)
    cv2.putText(frame, f"Original - Brightness: {brightness:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(enhanced_color, f"Enhanced - Max: {max_val}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    # Show both original and enhanced
    combined = np.hstack([frame, enhanced_color])
    cv2.imshow('Camera Feed (Original | Enhanced) - Press Q to quit', combined)
    
    frame_count += 1
    
    if frame_count % 30 == 0:
        print(f"Frame {frame_count}: brightness={brightness:.2f}, max={max_val}, good={good_frames}, black={black_frames}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\nStats:")
print(f"  Total frames: {frame_count}")
print(f"  Good frames: {good_frames}")
print(f"  Black frames: {black_frames}")
if frame_count > 0:
    print(f"  Success rate: {100*good_frames/frame_count:.1f}%")
