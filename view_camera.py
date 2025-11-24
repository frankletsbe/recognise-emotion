"""
Simple camera viewer - shows whatever the camera sees
"""
import cv2
import numpy as np

print("Opening camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Failed to open camera")
    exit(1)

print("Camera opened!")
print("Showing camera feed... Press 'q' to quit\n")

# Try to adjust settings
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
cap.set(cv2.CAP_PROP_EXPOSURE, -5)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
cap.set(cv2.CAP_PROP_CONTRAST, 150)
cap.set(cv2.CAP_PROP_GAIN, 100)

frame_count = 0

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to read frame")
        break
    
    # Enhance the image to make it more visible
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Try to enhance contrast
    enhanced = cv2.equalizeHist(gray)
    enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    # Calculate stats
    brightness = np.mean(gray)
    max_val = np.max(gray)
    
    # Add text overlay
    cv2.putText(frame, f"Original - Brightness: {brightness:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(enhanced_color, f"Enhanced - Max: {max_val}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Show both original and enhanced
    combined = np.hstack([frame, enhanced_color])
    cv2.imshow('Camera Feed (Original | Enhanced) - Press Q to quit', combined)
    
    frame_count += 1
    
    if frame_count % 30 == 0:
        print(f"Frame {frame_count}: brightness={brightness:.2f}, max={max_val}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\nShowed {frame_count} frames")
