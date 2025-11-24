"""
Camera Reset Utility
This script helps reset the camera by releasing all OpenCV connections
"""
import cv2
import time

def reset_camera(camera_index=0):
    """
    Reset camera by opening and closing it multiple times
    """
    print(f"Resetting camera {camera_index}...")
    
    # Try to release any existing connections
    for i in range(3):
        print(f"  Attempt {i+1}/3: Opening and releasing camera...")
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        time.sleep(0.5)
        cap.release()
        time.sleep(0.5)
    
    print("Camera reset complete!")
    print("\nNow testing camera with proper initialization...")
    
    # Open camera with proper initialization
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("ERROR: Failed to open camera")
        return False
    
    # Set properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Wait for camera to initialize
    print("Waiting 3 seconds for camera to initialize...")
    time.sleep(3)
    
    # Discard first few frames (they're often black)
    print("Discarding first 10 frames...")
    for i in range(10):
        ret, frame = cap.read()
        time.sleep(0.1)
    
    # Test actual frames
    print("\nTesting next 5 frames:")
    success_count = 0
    for i in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            import numpy as np
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            max_val = np.max(gray)
            print(f"  Frame {i+1}: brightness={brightness:.2f}, max={max_val}")
            if brightness > 10:  # Not a black frame
                success_count += 1
        else:
            print(f"  Frame {i+1}: Failed to read")
        time.sleep(0.2)
    
    cap.release()
    cv2.destroyAllWindows()
    
    if success_count >= 3:
        print(f"\n✓ Camera is working! ({success_count}/5 good frames)")
        return True
    else:
        print(f"\n✗ Camera still having issues ({success_count}/5 good frames)")
        return False

if __name__ == "__main__":
    reset_camera(0)
