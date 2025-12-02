import cv2

# Try different camera indices and backends
camera_configs = [
    (0, cv2.CAP_DSHOW),  # DirectShow backend (more reliable on Windows)
    (0, cv2.CAP_MSMF),   # Media Foundation backend
    (1, cv2.CAP_DSHOW),  # Try second camera with DirectShow
    (1, cv2.CAP_MSMF),   # Try second camera with MSMF
    (0, cv2.CAP_ANY),    # Let OpenCV choose backend
]

print("Testing webcam configurations...")
for cam_index, backend in camera_configs:
    print(f"\nTrying camera {cam_index} with backend {backend}...")
    cap = cv2.VideoCapture(cam_index, backend)
    
    if cap.isOpened():
        # Test if we can actually read a frame
        ret, test_frame = cap.read()
        if ret and test_frame is not None:
            print(f"✓ SUCCESS: Camera {cam_index} with backend {backend} works!")
            print(f"  Frame shape: {test_frame.shape}")
            cap.release()
            break
        else:
            print(f"✗ Camera opened but cannot read frames")
            cap.release()
    else:
        print(f"✗ Failed to open camera {cam_index}")
        if cap is not None:
            cap.release()
else:
    print("\n" + "="*60)
    print("ERROR: Could not open webcam with any configuration.")
    print("="*60)
