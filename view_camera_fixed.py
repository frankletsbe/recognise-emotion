"""
Fixed camera viewer - works around OpenCV black frame issues
"""
import cv2
import numpy as np
import time

print("Opening camera with compatibility mode...")

# Try different backends in order of preference
backends = [
    (cv2.CAP_MSMF, "Media Foundation"),
    (cv2.CAP_DSHOW, "DirectShow"),
    (cv2.CAP_ANY, "Auto")
]

cap = None
for backend, name in backends:
    print(f"Trying {name} backend...")
    cap = cv2.VideoCapture(0, backend)
    if cap.isOpened():
        print(f"✓ Success with {name}")
        break
    else:
        print(f"✗ Failed with {name}")

if not cap or not cap.isOpened():
    print("ERROR: Could not open camera with any backend")
    exit(1)

# Set properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# CRITICAL: Set buffer size to 1 (get latest frame, not buffered old frames)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print("\nInitializing camera...")
time.sleep(3)  # Wait for camera to warm up

# Flush buffer by reading and discarding frames
print("Flushing frame buffer...")
for i in range(30):
    cap.grab()  # Just grab, don't decode
    time.sleep(0.033)  # ~30fps

print("\nCamera ready! Press 'q' to quit\n")

frame_count = 0
black_count = 0
good_count = 0

while True:
    # Use grab() then retrieve() for better frame sync
    if not cap.grab():
        print("Failed to grab frame")
        break
    
    ret, frame = cap.retrieve()
    
    if not ret or frame is None:
        print("Failed to retrieve frame")
        continue
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    max_val = np.max(gray)
    
    # Track frame quality
    if brightness < 5:
        black_count += 1
        status = "BLACK FRAME!"
        color = (0, 0, 255)  # Red
    else:
        good_count += 1
        status = "Good"
        color = (0, 255, 0)  # Green
    
    # Enhanced version
    enhanced = cv2.equalizeHist(gray)
    enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    # Add overlays
    cv2.putText(frame, f"Original - Brightness: {brightness:.1f} - {status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(enhanced_color, f"Enhanced - Max: {max_val}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Show side by side
    combined = np.hstack([frame, enhanced_color])
    cv2.imshow('Camera Feed - Press Q to quit', combined)
    
    frame_count += 1
    
    # Print stats every 30 frames
    if frame_count % 30 == 0:
        success_rate = 100 * good_count / frame_count if frame_count > 0 else 0
        print(f"Frame {frame_count}: brightness={brightness:.2f}, good={good_count}, black={black_count}, success={success_rate:.1f}%")
    
    # Small delay to prevent CPU overload
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n=== Final Stats ===")
print(f"Total frames: {frame_count}")
print(f"Good frames: {good_count}")
print(f"Black frames: {black_count}")
if frame_count > 0:
    print(f"Success rate: {100*good_count/frame_count:.1f}%")
