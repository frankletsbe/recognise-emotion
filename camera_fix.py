"""
Camera Fix - Handle Windows camera access issues
"""
import cv2
import numpy as np
import time

print("=== Camera Access Fix ===\n")

# Step 1: Make sure Windows Camera app is closed
print("IMPORTANT: Please close the Windows Camera app if it's running!")
print("Press Enter when ready...")
input()

# Step 2: Try to open and configure camera properly
print("\nOpening camera with DirectShow...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Failed to open camera")
    exit(1)

print("✓ Camera opened")

# Step 3: Set camera properties BEFORE reading frames
print("\nConfiguring camera properties...")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get fresh frames

# Try to enable auto exposure and auto white balance
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto mode
cap.set(cv2.CAP_PROP_AUTO_WB, 1)  # Auto white balance

# Try to set exposure manually if auto doesn't work
cap.set(cv2.CAP_PROP_EXPOSURE, -5)  # Negative values for auto, or try positive values

print("✓ Properties set")

# Step 4: Flush the buffer by reading and discarding frames
print("\nFlushing camera buffer...")
for i in range(10):
    cap.read()
time.sleep(0.5)

# Step 5: Read and display frames
print("\nReading frames...")
frame_count = 0
max_frames = 100

while frame_count < max_frames:
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print(f"❌ Failed to read frame {frame_count + 1}")
        break
    
    # Check frame quality
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    max_val = np.max(gray)
    non_zero = np.count_nonzero(gray)
    
    # Add status overlay
    status_text = f"Frame: {frame_count+1} | Brightness: {mean_brightness:.1f} | Max: {max_val} | Non-zero: {non_zero}"
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    if mean_brightness < 1:
        cv2.putText(frame, "WARNING: Very dark image!", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Display
    cv2.imshow('Camera Test - Press Q to quit', frame)
    
    # Print stats every 10 frames
    if frame_count % 10 == 0:
        print(f"Frame {frame_count}: brightness={mean_brightness:.2f}, max={max_val}, non-zero={non_zero}/{gray.size}")
    
    frame_count += 1
    
    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n✓ Displayed {frame_count} frames")

if mean_brightness < 1:
    print("\n⚠️  ISSUE DETECTED: Camera is returning very dark frames")
    print("\nPossible solutions:")
    print("1. Make sure Windows Camera app is completely closed")
    print("2. Check camera privacy settings: Settings > Privacy > Camera")
    print("3. Try unplugging and replugging the camera (if external)")
    print("4. Update camera drivers")
    print("5. Restart your computer")
else:
    print("\n✅ Camera is working!")
