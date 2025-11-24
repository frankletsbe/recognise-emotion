"""
Force camera exposure and gain settings
"""
import cv2
import numpy as np
import time

print("=== Camera Exposure Fix ===\n")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Failed to open camera")
    exit(1)

print("Camera opened\n")

# Get current settings
print("Current camera settings:")
print(f"  Exposure: {cap.get(cv2.CAP_PROP_EXPOSURE)}")
print(f"  Brightness: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
print(f"  Contrast: {cap.get(cv2.CAP_PROP_CONTRAST)}")
print(f"  Gain: {cap.get(cv2.CAP_PROP_GAIN)}")
print(f"  Auto Exposure: {cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)}")

# Try different exposure values
exposure_values = [0.25, 0.5, 0.75, -1, -2, -3, -4, -5, -6, -7, -8, 1, 2, 3, 4, 5]

print("\nTrying different exposure values...\n")

best_brightness = 0
best_exposure = None
best_frame = None

for exp_val in exposure_values:
    # Set exposure
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
    cap.set(cv2.CAP_PROP_EXPOSURE, exp_val)
    cap.set(cv2.CAP_PROP_GAIN, 50)  # Increase gain
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Mid brightness
    
    # Flush buffer
    for _ in range(5):
        cap.read()
    
    time.sleep(0.2)
    
    # Read frame
    ret, frame = cap.read()
    
    if not ret or frame is None:
        continue
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    
    print(f"Exposure {exp_val:6.2f}: brightness = {brightness:6.2f}")
    
    if brightness > best_brightness:
        best_brightness = brightness
        best_exposure = exp_val
        best_frame = frame.copy()

print(f"\nBest exposure value: {best_exposure} (brightness: {best_brightness:.2f})")

if best_frame is not None and best_brightness > 10:
    print("\nDisplaying best result... Press any key to close")
    cv2.imshow('Best Camera Result', best_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("\n✅ Found working exposure setting!")
    print(f"Use: cap.set(cv2.CAP_PROP_EXPOSURE, {best_exposure})")
else:
    print("\n❌ Could not find good exposure setting")
    print("\nThis indicates a camera driver issue. Try:")
    print("1. Update camera drivers from Device Manager")
    print("2. Check Windows Privacy Settings → Camera")
    print("3. Try a different camera if available")
    print("4. Reinstall OpenCV: pip uninstall opencv-python && pip install opencv-python")

cap.release()
