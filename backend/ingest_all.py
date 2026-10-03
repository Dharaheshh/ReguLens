
import glob
import requests
import os

docs = glob.glob("D:/Projects/Dossier_docs/*.pdf")
url = "http://localhost:8000/api/v1/documents"

for f in docs: # Ingest all documents
    print(f"Ingesting {os.path.basename(f)}...")
    with open(f, "rb") as file_data:
        res = requests.post(url, files={"file": file_data}, data={"doc_type": "scientific_paper", "is_synthetic": "true"})
        print(res.status_code, res.json() if res.status_code != 200 else "OK")

