import platform
import sys
import os

try:
    import cv2
    opencv_installed = True
except ImportError:
    opencv_installed = False

print("### Python Environment Verification ###")
print("-" * 35)

# Python Version
print(f"Python Version: {sys.version.splitlines()[0]}")
print(f"Python Executable: {sys.executable}")

# Platform Architecture
print(f"Platform Machine (CPU Arch): {platform.machine()}")
print(f"Platform System: {platform.system()}")
print(f"Platform Release: {platform.release()}")

# OpenCV Status
if opencv_installed:
    print(f"OpenCV Installed: Yes")
    print(f"OpenCV Version: {cv2.__version__}")
    # Check if OpenCV is built for ARM64 (this is a heuristic, not foolproof)
    if "arm" in cv2.__version__.lower() or "arm64" in platform.machine().lower():
        print("OpenCV Architecture: Likely ARM64 compatible")
    else:
        print("OpenCV Architecture: May be x86 (AMD64) under emulation")
else:
    print("OpenCV Installed: No (or failed to import)")

print("-" * 35)
print("\nRecommendations:")
if platform.machine() == 'AMD64':
    print("- You are running an x86 (AMD64) Python environment.")
    print("  For optimal performance and camera compatibility on your Yoga Slim 7x (ARM-based),")
    print("  it is highly recommended to install a native ARM64 Python and OpenCV.")
    print("  (See previous instructions for installing Python ARM64 from python.org).")
elif platform.machine() == 'ARM64' and not opencv_installed:
    print("- You have ARM64 Python, but OpenCV is not installed.")
    print("  Activate your ARM64 environment and run: pip install opencv-python")
elif platform.machine() == 'ARM64' and opencv_installed:
    print("- You have ARM64 Python and OpenCV is installed.")
    print("  This is the ideal setup for your Yoga Slim 7x.")
    print("  Proceed with testing your camera script using cv2.CAP_MSMF backend.")
else:
    print("- Current setup is unusual. Please review your Python installation.")