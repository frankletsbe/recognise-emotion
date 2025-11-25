import cv2
import platform
from deepface import DeepFace

print("machine:", platform.machine())
print("cv2:", cv2.__version__)

# External camera: index 1, DirectShow backend
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
print("Opened:", cap.isOpened())
if not cap.isOpened():
    raise RuntimeError("Cannot open external camera (index 1, CAP_DSHOW)")

# Load Haar Cascade for face detection
face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(face_cascade_path)

if face_cascade.empty():
    raise RuntimeError(f"Failed to load face cascade from {face_cascade_path}")

# Throttling parameters
frame_count = 0
EMOTION_EVERY_N_FRAMES = 20  # adjust this (higher = slower updates)

# Cache of last emotion result per face (just one face here)
last_emotion = None
last_confidence = None

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Failed to grab frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    frame_count += 1
    run_emotion = (frame_count % EMOTION_EVERY_N_FRAMES == 0)

    for (x, y, w, h) in faces:
        # Draw face box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        face_roi = frame[y:y + h, x:x + w]

        if run_emotion:
            try:
                result = DeepFace.analyze(
                    face_roi,
                    actions=['emotion'],
                    enforce_detection=False
                )
                if isinstance(result, list):
                    result = result[0]

                emotion = result['dominant_emotion']
                confidence = result['emotion'][emotion]

                last_emotion = emotion
                last_confidence = confidence

            except Exception:
                # Keep previous result if any
                pass

        # Draw last known emotion (even if we didn't re-run this frame)
        if last_emotion is not None and last_confidence is not None:
            text = f"{last_emotion}: {last_confidence:.1f}%"
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Face & Emotion Detection (Throttled)", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()