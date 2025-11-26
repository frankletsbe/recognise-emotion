import tensorflow as tf
import tf2onnx

# Load your Keras model
model = tf.keras.models.load_model("models/final/emotion_recognition_ft_20251116_115814.keras")

# Convert to ONNX
spec = (tf.TensorSpec((None, 48, 48, 1), tf.float32, name="input"),)
onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=13)

# Save
with open("emotion_model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

print("Model converted to ONNX successfully!")