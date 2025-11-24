"""
Test all camera indices to find working camera
"""
import cv2
import numpy as np

print("=== Testing Camera Indices ===\n")

for camera_index in range(5):  # Test indices 0-4
    print(f"\nTrying camera index {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"  ✗ Camera {camera_index} not available")
        continue
    
    print(f"  ✓ Camera {camera_index} opened")
    
    # Read a frame
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print(f"  ✗ Failed to read frame")
        cap.release()
        continue
    
    # Check brightness
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    non_zero = np.count_nonzero(gray)
    
    print(f"  Brightness: {brightness:.2f}")
    print(f"  Non-zero pixels: {non_zero}/{gray.size}")
    
    if brightness > 10:
        print(f"  ✅ Camera {camera_index} looks good!")
        print(f"\n  Displaying preview... Press any key to continue")
        cv2.imshow(f'Camera {camera_index}', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"  ⚠️  Camera {camera_index} is very dark")
    
    cap.release()

print("\n" + "="*50)
print("Test complete!")
