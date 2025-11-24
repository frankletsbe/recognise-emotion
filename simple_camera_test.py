"""
Simplified Camera Diagnostic - Find why screen is black
"""
import cv2
import numpy as np

def test_camera_backend(backend_name, backend_code):
    """Test a specific camera backend"""
    print(f"\n{'='*60}")
    print(f"Testing: {backend_name}")
    print('='*60)
    
    cap = cv2.VideoCapture(0, backend_code)
    
    if not cap.isOpened():
        print(f"❌ Failed to open camera with {backend_name}")
        return False
    
    print(f"✓ Camera opened with {backend_name}")
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("❌ Failed to read frame")
        cap.release()
        return False
    
    # Analyze the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(f"\nFrame stats:")
    print(f"  Shape: {frame.shape}")
    print(f"  Mean brightness: {np.mean(gray):.2f}")
    print(f"  Min: {np.min(gray)}, Max: {np.max(gray)}")
    print(f"  Std dev: {np.std(gray):.2f}")
    print(f"  Non-zero pixels: {np.count_nonzero(gray)} / {gray.size}")
    
    # Show the window
    print(f"\nDisplaying window... Press any key to continue")
    cv2.imshow(f'Camera Test - {backend_name}', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    cap.release()
    return True

# Test different backends
print("=== Camera Backend Diagnostic ===\n")

backends = [
    ("DirectShow (Windows)", cv2.CAP_DSHOW),
    ("Media Foundation (Windows)", cv2.CAP_MSMF),
    ("Default/Auto", cv2.CAP_ANY),
]

for name, code in backends:
    test_camera_backend(name, code)

print("\n" + "="*60)
print("Diagnostic complete!")
print("="*60)
