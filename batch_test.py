import os
import requests

resume_dir = r'C:\Users\khushi tyagi\Major project -2 (JOB - TALK)\backend\resume\data\data\INFORMATION-TECHNOLOGY'

URL = "http://127.0.0.1:8000/upload_resume/"

print("Starting Batch Testing Phase...")

count = 0
for filename in os.listdir(resume_dir):
    if filename.endswith(".pdf") and count < 30:
        file_path = os.path.join(resume_dir, filename)
        
        with open(file_path, 'rb') as f:
            
            payload = {'user_id': 1, 'job_id': 11}
            files = [('file', (filename, f, 'application/pdf'))]
            
            try:
                response = requests.post(URL, data=payload, files=files)
                if response.status_code == 200:
                    result = response.json()
                    print(f"[{count+1}] Processed: {filename} | Score: {result['match_score']}")
                else:
                    print(f"Failed to process {filename}: {response.text}")
            except Exception as e:
                print(f"Error connecting to server: {e}")
        
        count += 1

print(f"\nBatch Testing Complete. {count} candidate profiles generated in MySQL.")