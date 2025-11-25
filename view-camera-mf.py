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

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Failed to grab frame")
        break

    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    # Process each detected face
    for (x, y, w, h) in faces:
        # Draw green box around face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Extract face ROI for emotion detection
        face_roi = frame[y:y+h, x:x+w]

        try:
            # Analyze emotion using DeepFace
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
            
            # Get dominant emotion and confidence
            if isinstance(result, list):
                result = result[0]
            
            emotion = result['dominant_emotion']
            confidence = result['emotion'][emotion]

            # Display emotion and confidence above the box
            text = f"{emotion}: {confidence:.1f}%"
            cv2.putText(frame, text, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        except Exception as e:
            # If emotion detection fails, just skip
            pass

    cv2.imshow("Face & Emotion Detection", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()