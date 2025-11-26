import requests
import os

def test_prediction():
    url = 'http://127.0.0.1:5000/predict'
    image_path = 'C:/Users/marty/.gemini/antigravity/brain/a436ccb8-6a8b-45d5-b0c5-39fe5c037392/uploaded_image_1764134446059.png'
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    print(f"Testing prediction with {image_path}...")
    
    try:
        with open(image_path, 'rb') as img:
            files = {'file': img}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("Success!")
            print(f"Prediction: {data.get('prediction')}")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Box: {data.get('box')}")
            
            if data.get('box'):
                print("PASS: Bounding box returned.")
            else:
                print("FAIL: No bounding box returned.")
        else:
            print(f"Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_prediction()
