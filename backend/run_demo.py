import os
import sys
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import RegulatoryQuery, Evidence
from app.retrieval.hybrid_search import hybrid_search
from app.generation.requirement_extraction import extract_requirements
from app.generation.response_generation import generate_response
from app.validation.citation_validator import validate_citations

def main():
    db = SessionLocal()
    try:
        
        query_text = (
            "Provide evidence supporting the microbiological safety of the "
            "cultivated-cell product and describe the controls used during production."
        )
        print(f"\n--- QUERY ---\n{query_text}")
        q = RegulatoryQuery(query_text=query_text)
        db.add(q)
        db.flush()

        # 2. Extract Requirements (Task-011)
        print("\n--- EXTRACTING REQUIREMENTS (LLM Call 1) ---")
        reqs = extract_requirements(db, q.id, query_text)
        for r in reqs:
            print(f"[{r.req_code}] {r.description} (Keywords: {r.keywords})")

        # 3. Retrieve Evidence for the first requirement (Task-009)
        if not reqs:
            print("No requirements extracted.")
            return
            
        search_query = f"{reqs[0].description} {' '.join(reqs[0].keywords)}"
        print(f"\n--- HYBRID RETRIEVAL (Task-009) for: {reqs[0].req_code} ---")
        results = hybrid_search(db, search_query, k=3)
        evidence_pack = []
        for r in results:
            print(f"Match: Chunk {r.chunk_id} (Score: {r.score:.3f})")
            if r.evidence_code:
                evidence_pack.append({
                    "evidence_code": r.evidence_code,
                    "text": r.content,
                })

        if not evidence_pack:
            print("No evidence retrieved. Please ensure you have ingested a document first (e.g. using POST /api/v1/documents)!")
            return

        # 4. Generate Response (Task-012)
        print("\n--- GENERATING RESPONSE (LLM Call 2) ---")
        req_dicts = [{"req_code": r.req_code, "description": r.description} for r in reqs]
        response, claims = generate_response(db, q.id, query_text, req_dicts, evidence_pack)
        
        print("\n--- DRAFT TEXT ---")
        print(response.draft_text)
        print("\n--- CLAIMS ---")
        for c in claims:
            print(f"[{c.claim_code}] {c.claim_text}")
            print(f"  Req: {c._req_code} | Proposed Citations: {c._cited_evidence_codes}")

        db.commit()
    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
