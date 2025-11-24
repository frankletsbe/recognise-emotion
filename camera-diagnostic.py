"""
Camera Diagnostic Tool
Checks if the camera is working, captures test images, and validates facial detection.
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Load Face Cascade Classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print("=== Camera Diagnostic Tool ===\n")
print(f"Face cascade loaded: {face_cascade.empty() == False}\n")

def check_frame_quality(frame):
    """
    Check if frame is valid and not a black screen.
    Returns: (is_valid, mean_brightness, details)
    """
    if frame is None or frame.size == 0:
        return False, 0, "Frame is None or empty"
    
    # Calculate mean brightness
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    min_val = np.min(gray)
    max_val = np.max(gray)
    
    # Check if it's a completely black screen (very low max value)
    if max_val < 50:
        return False, mean_brightness, f"Black screen detected (max pixel value {max_val} < 50)"
    
    # Check if there's any variation (not a solid color)
    std_dev = np.std(gray)
    if std_dev < 0.5:
        return False, mean_brightness, "No variation in image (solid color)"
    
    return True, mean_brightness, f"Valid frame (mean={mean_brightness:.2f}, min={min_val}, max={max_val}, std={std_dev:.2f})"

def detect_faces(frame):
    """
    Detect faces in the frame.
    Returns: (num_faces, faces_array)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    return len(faces), faces

def main():
    # Test 1: Try to open camera with DirectShow backend
    print("1. Testing DirectShow backend (cv2.CAP_DSHOW)...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("   ✗ Failed to open camera with DirectShow")
        print("\n2. Trying default backend...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("   ✗ Failed to open camera with default backend")
            print("\n❌ DIAGNOSTIC FAILED: Cannot access camera")
            return 1
        else:
            print("   ✓ Camera opened with default backend")
    else:
        print("   ✓ Camera opened with DirectShow")
    
    # Set camera properties to help with initialization
    print("\n   Setting camera properties...")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    print("   ✓ Camera properties set")
    
    # Warm up the camera (let it adjust exposure) - extended warm-up
    print("\n   Warming up camera (allowing exposure adjustment)...")
    import time
    time.sleep(2)  # Give camera hardware time to initialize
    
    for i in range(20):
        ret, frame = cap.read()
        if i % 5 == 0:
            print(f"   Warming up... frame {i+1}/20")
            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                print(f"   Current brightness: {brightness:.2f}")
    print("   ✓ Camera warm-up complete")
    
    # Test 2: Read frames and check content
    print("\n2. Reading frames and checking content...")
    valid_frames = 0
    black_frames = 0
    
    for i in range(15):
        ret, frame = cap.read()
        if not ret:
            print(f"   ✗ Failed to read frame {i+1}")
            continue
        
        is_valid, brightness, details = check_frame_quality(frame)
        
        if is_valid:
            valid_frames += 1
            print(f"   Frame {i+1}: mean={brightness:.2f}, min={np.min(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))}, max={np.max(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))}, shape={frame.shape}")
        else:
            black_frames += 1
            print(f"   ✗ Frame {i+1}: {details}")
    
    if valid_frames == 0:
        print("\n❌ DIAGNOSTIC FAILED: All frames are invalid or black")
        cap.release()
        return 1
    
    print(f"\n   ✓ Valid frames: {valid_frames}/15")
    if black_frames > 0:
        print(f"   ⚠ Black/invalid frames: {black_frames}/15")
    
    # Test 3: Capture a test image and detect faces
    print("\n3. Testing with display window...")
    print("   Opening window... Press 'q' to close")
    
    face_detected = False
    frame_count = 0
    max_frames = 100
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            print("   ✗ Failed to capture frame")
            break
        
        # Detect faces
        num_faces, faces = detect_faces(frame)
        
        if num_faces > 0 and not face_detected:
            face_detected = True
            print(f"   ✓ Face detected! ({num_faces} face(s) found)")
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Add status text
        is_valid, brightness, _ = check_frame_quality(frame)
        status_text = f"Brightness: {brightness:.1f} | Faces: {num_faces} | Frame: {frame_count+1}/{max_frames}"
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display
        cv2.imshow('Camera Diagnostic', frame)
        
        frame_count += 1
        
        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    print(f"   Displayed {frame_count} frames")
    
    # Test 4: Save a diagnostic image
    print("\n4. Saving diagnostic image...")
    ret, frame = cap.read()
    if ret:
        output_path = Path(__file__).parent / "diagnostic_frame.jpg"
        cv2.imwrite(str(output_path), frame)
        print(f"   ✓ Saved to: {output_path}")
        
        # Check the saved image
        is_valid, brightness, details = check_frame_quality(frame)
        print(f"   Image quality: {details}")
        
        num_faces, _ = detect_faces(frame)
        if num_faces > 0:
            print(f"   ✓ {num_faces} face(s) detected in saved image")
        else:
            print(f"   ⚠ No faces detected in saved image (this is OK if no one is in frame)")
    else:
        print("   ✗ Failed to capture image for saving")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Final summary
    print("\n=== Diagnostic Complete ===")
    if valid_frames > 10 and not (black_frames > 5):
        print("✅ Camera is working properly!")
        if face_detected:
            print("✅ Face detection is working!")
        else:
            print("⚠️  No faces detected (make sure you're in front of the camera)")
        return 0
    else:
        print("⚠️  Camera may have issues (many black frames detected)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
