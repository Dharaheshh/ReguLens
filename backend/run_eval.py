import os
import time
import glob
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Bypass auth for eval script
os.environ["PYTEST_CURRENT_TEST"] = "1"

def ingest():
    print("--- INGESTION PHASE ---")
    files = glob.glob("D:/Projects/Dossier_docs/*.pdf")
    # Take paper1, paper10, paper11
    targets = ["paper1.pdf", "paper10.pdf", "paper11.pdf"]
    to_ingest = [f for f in files if os.path.basename(f) in targets]
    
    for f in to_ingest:
        fname = os.path.basename(f)
        print(f"Ingesting {fname}...")
        with open(f, "rb") as file_data:
            res = client.post("/api/v1/documents", files={"file": (fname, file_data, "application/pdf")}, data={"doc_type": "scientific_paper", "is_synthetic": "true"})
            if res.status_code not in (200, 201):
                print(f"Failed to ingest {fname}: {res.text}")

def evaluate():
    print("\n--- EVALUATION PHASE ---")
    questions = [
        ("What are the microbiological safety considerations for cultivated meat?", "paper1.pdf", True),
        ("How do extruded plant protein scaffold structures support myoblast cell growth?", "paper10.pdf", True),
        ("Can bovine placentome-derived extracellular matrix be used as a sustainable 3D scaffold?", "paper11.pdf", True),
        ("What is the capital of France?", None, False) # Should trigger insufficient evidence
    ]
    
    total = len(questions)
    passed = 0
    total_latency = 0
    
    for q, expected_doc, expects_response in questions:
        print(f"\nQuery: {q}")
        start = time.time()
        res = client.post("/api/v1/queries", json={"query_text": q})
        end = time.time()
        latency = end - start
        total_latency += latency
        
        if res.status_code != 200:
            print(f"  [ERROR] API failed with {res.status_code}: {res.text}")
            continue
            
        data = res.json()
        
        if not expects_response:
            if data["sufficiency_status"] == "INSUFFICIENT":
                print(f"  [PASS] Correctly blocked by Evidence Gate (Latency: {latency:.2f}s)")
                passed += 1
            else:
                print(f"  [FAIL] Expected block, but generated response (Latency: {latency:.2f}s)")
            continue
            
        # Expecting a valid response
        if data["sufficiency_status"] == "INSUFFICIENT":
            print(f"  [FAIL] Falsely blocked by Evidence Gate! (Latency: {latency:.2f}s)")
            continue
            
        claims = data.get("claims", [])
        if not claims:
            print(f"  [FAIL] Generated response but no claims extracted (Latency: {latency:.2f}s)")
            continue
            
        # Check if citations map to expected_doc
        found_expected = False
        cited_docs = set()
        
        for c in claims:
            for cit in c.get("citations", []):
                # Retrieve the evidence to see which doc it belongs to
                ev_res = client.get(f"/api/v1/evidence/{cit['evidence_code']}")
                if ev_res.status_code == 200:
                    fname = ev_res.json()["document_filename"]
                    cited_docs.add(fname)
                    if fname == expected_doc:
                        found_expected = True
                        
        if found_expected:
            print(f"  [PASS] Correctly cited {expected_doc} (Latency: {latency:.2f}s)")
            passed += 1
        else:
            print(f"  [FAIL] Cited {cited_docs} instead of {expected_doc} (Latency: {latency:.2f}s)")

    print("\n--- RESULTS ---")
    print(f"Accuracy (Recall@1 / Gate Accuracy): {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"Average Latency: {total_latency/total:.2f} seconds")

if __name__ == "__main__":
    ingest()
    evaluate()
