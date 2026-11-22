import requests
import time

# Wait a moment to ensure the server is fully up
time.sleep(2)

# A real one-page synthetic lab report (same as Docs/demo-report.pdf).
dummy_file_path = "test_report.pdf"

url = "http://127.0.0.1:8000/api/v1/intake/upload"

print(f"Uploading {dummy_file_path} to {url}...")
try:
    with open(dummy_file_path, "rb") as f:
        files = {"file": (dummy_file_path, f, "application/pdf")}
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print(f"Failed to connect or upload: {e}")
