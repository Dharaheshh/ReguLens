import os
import sys
import requests
import glob

# Change this to the path where your real dossier PDFs are located
DOSSIER_FOLDER = r"D:\Projects\Dossier_docs" 
API_URL = "http://localhost:8000/api/v1/documents"

def upload_all_pdfs():
    if not os.path.exists(DOSSIER_FOLDER):
        print(f"Folder not found: {DOSSIER_FOLDER}")
        print("Please edit the DOSSIER_FOLDER variable in this script!")
        return

    pdf_files = glob.glob(os.path.join(DOSSIER_FOLDER, "*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {DOSSIER_FOLDER}")
        return

    print(f"Found {len(pdf_files)} PDFs. Starting ingestion...\n")

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Uploading {filename}...")
        
        with open(pdf_path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            data = {
                "doc_type": "scientific_paper", # Change if needed
                "is_synthetic": "false"         # These are real!
            }
            
            try:
                response = requests.post(API_URL, files=files, data=data)
                if response.status_code == 201:
                    print(f"  ✅ Success: {response.json()['document_id']}")
                else:
                    print(f"  ❌ Failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    upload_all_pdfs()
