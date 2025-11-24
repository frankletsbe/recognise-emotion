import cv2
import numpy as np
import time

print("=== Camera Diagnostic Tool ===\n")

# Load Face Cascade Classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
print(f"Face cascade loaded: {not face_cascade.empty()}\n")

# Try DirectShow backend
print("1. Testing DirectShow backend (cv2.CAP_DSHOW)...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("   ✗ Failed to open camera with DirectShow")
else:
    print("   ✓ Camera opened with DirectShow")
    
    # Read multiple frames and check them
    print("\n2. Reading frames and checking content...")
    for i in range(15):
        ret, frame = cap.read()
        if ret and frame is not None:
            mean_val = frame.mean()
            max_val = frame.max()
            min_val = frame.min()
            print(f"   Frame {i+1}: mean={mean_val:.2f}, min={min_val}, max={max_val}, shape={frame.shape}")
            
            if mean_val > 1.0:
                print(f"   ✓ Frame {i+1} appears valid (not black)!")
                
                # Save a sample frame
                if i == 10:
                    cv2.imwrite('diagnostic_frame.jpg', frame)
                    print(f"   Saved frame to diagnostic_frame.jpg")
        else:
            print(f"   ✗ Frame {i+1}: Failed to read")
        
        time.sleep(0.1)  # Small delay between reads
    
    cap.release()

print("\n3. Testing with display window...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("   Opening window... Press 'q' to close")
    
    frame_count = 0
    while frame_count < 100:  # Auto-close after 100 frames
        ret, frame = cap.read()
        if ret and frame is not None:
            frame_count += 1
            
            # Convert to grayscale for face detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw green boxes around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Face", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add diagnostic info to frame
            mean_val = frame.mean()
            cv2.putText(frame, f"Frame: {frame_count}, Mean: {mean_val:.1f}, Faces: {len(faces)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Camera Diagnostic', frame)
            
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        else:
            print(f"   ✗ Failed to read frame {frame_count}")
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"   Displayed {frame_count} frames")

print("\n=== Diagnostic Complete ===")
