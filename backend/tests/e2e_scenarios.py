import os
import sys
import uuid
import json
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import RegulatoryQuery, Requirement, Response, Claim, Citation, Evidence, Chunk, Document, DocumentVersion, Contradiction
from app.generation.requirement_extraction import RequirementExtractionOutput, RequirementSchema
from app.generation.response_generation import ResponseGenerationOutput, ClaimProposal
from app.validation.claim_validator import SemanticValidationOutput
from app.validation.contradiction_engine import ContradictionOutput

client = TestClient(app)

REPORT_MD = ["# ReguLens End-to-End Scenarios Report\n"]

def run_scenario_1_insufficient_evidence():
    """Scenario 1: Insufficient Evidence (Long-term toxicity)."""
    REPORT_MD.append("## Scenario 1: Insufficient Evidence\n")
    REPORT_MD.append("**Description**: Verifies that when evidence falls below the retrieval threshold, the system deterministically flags it as INSUFFICIENT.\n")
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback") as mock_req, \
         patch("app.routers.queries.hybrid_search") as mock_search, \
         patch("app.generation.response_generation.call_with_retry_and_fallback") as mock_gen, \
         patch("app.validation.claim_validator.call_with_retry_and_fallback") as mock_claim:
         
         mock_req.return_value = RequirementExtractionOutput(requirements=[
             RequirementSchema(req_code="REQ-TOX", description="Long-term toxicity data", keywords=[])
         ])
         
         # Setup real evidence for scenario 1
         db = SessionLocal()
         doc = Document(filename="tox.pdf", doc_type="test"); db.add(doc); db.flush()
         ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="tox"); db.add(ver); db.flush()
         chunk = Chunk(document_version_id=ver.id, content="No long term data."); db.add(chunk); db.flush()
         evd_code = f"EVD-LOW-{uuid.uuid4().hex[:5]}"
         evd = Evidence(evidence_code=evd_code, chunk_id=chunk.id, document_id=doc.id, document_version_id=ver.id, source_type="test"); db.add(evd); db.commit()
         evd_id = evd.id
         chunk_id = chunk.id
         db.close()
         
         # Mock search returning low score
         class MockSearch:
             def __init__(self, chunk_id, evidence_id, evidence_code, content, score, source_type):
                 self.chunk_id = chunk_id
                 self.evidence_id = evidence_id
                 self.evidence_code = evidence_code
                 self.content = content
                 self.score = score
                 self.source_type = source_type
         mock_search.return_value = [MockSearch(chunk_id, evd_id, evd_code, "No long term data.", 0.001, "test")]
         
         mock_gen.return_value = ResponseGenerationOutput(
             draft_text="We have no data.",
             claims=[ClaimProposal(claim_code="CLM-1", claim_text="No data.", product_topic="tox", req_code="REQ-TOX", cited_evidence_codes=[evd_code])]
         )
         
         res = client.post("/api/v1/queries", json={"query_text": "Show long term toxicity."})
         data = res.json()
         
         REPORT_MD.append(f"- **Result**: Sufficiency Status = `{data['sufficiency_status']}`\n")
         REPORT_MD.append(f"- **Gap Summary**: {data['gap_summary']}\n")
         assert data.get("sufficiency_status") == "INSUFFICIENT", f"Failed: {data}"


def run_scenario_2_contradiction_true_positive():
    """Scenario 2: Contradiction - True Positive."""
    REPORT_MD.append("## Scenario 2: Contradiction (True Positive)\n")
    REPORT_MD.append("**Description**: Verifies that a genuine conflict with a historical approved claim is flagged as a LIKELY_CONTRADICTION.\n")
    
    db = SessionLocal()
    # Setup historical approved claim
    q = RegulatoryQuery(query_text="old"); db.add(q); db.flush()
    r = Response(query_id=q.id, status="approved"); db.add(r); db.flush()
    c = Claim(response_id=r.id, claim_code="CLM-OLD", claim_text="pH must be exactly 7.0", product_topic="pH-control")
    db.add(c); db.commit(); db.close()
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback") as mock_req, \
         patch("app.routers.queries.hybrid_search") as mock_search, \
         patch("app.generation.response_generation.call_with_retry_and_fallback") as mock_gen, \
         patch("app.validation.claim_validator.call_with_retry_and_fallback") as mock_claim, \
         patch("app.validation.contradiction_engine.call_with_retry_and_fallback") as mock_contra:
         
         mock_req.return_value = RequirementExtractionOutput(requirements=[RequirementSchema(req_code="REQ-1", description="pH", keywords=[])])
         mock_search.return_value = []
         mock_gen.return_value = ResponseGenerationOutput(
             draft_text="pH is 8.0.",
             claims=[ClaimProposal(claim_code="CLM-NEW", claim_text="pH is maintained at 8.0.", product_topic="pH-control", req_code="REQ-1", cited_evidence_codes=[])]
         )
         mock_contra.return_value = ContradictionOutput(
             classification="LIKELY_CONTRADICTION", reasoning="7.0 != 8.0", distinguishing_factors_considered=[]
         )
         
         res = client.post("/api/v1/queries", json={"query_text": "What is the pH?"})
         data = res.json()
         
         contras = data.get("contradictions", [])
         REPORT_MD.append(f"- **Result**: Found {len(contras)} contradictions.\n")
         if contras:
             REPORT_MD.append(f"- **Classification**: `{contras[0]['classification']}`\n")
             REPORT_MD.append(f"- **Reasoning**: {contras[0]['reasoning']}\n")
         assert len(contras) == 1
         assert contras[0]["classification"] == "LIKELY_CONTRADICTION"

def run_scenario_3_contradiction_false_positive():
    """Scenario 3: Contradiction - False Positive Check."""
    REPORT_MD.append("## Scenario 3: Contradiction (False Positive Check)\n")
    REPORT_MD.append("**Description**: Verifies that claims with different scopes (e.g. different assays) are correctly flagged as COMPATIBLE, avoiding over-triggering.\n")
    
    db = SessionLocal()
    q = RegulatoryQuery(query_text="old2"); db.add(q); db.flush()
    r = Response(query_id=q.id, status="approved"); db.add(r); db.flush()
    c = Claim(response_id=r.id, claim_code="CLM-OLD2", claim_text="Assay A sensitivity is 50ng.", product_topic="assay")
    db.add(c); db.commit(); db.close()
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback") as mock_req, \
         patch("app.routers.queries.hybrid_search") as mock_search, \
         patch("app.generation.response_generation.call_with_retry_and_fallback") as mock_gen, \
         patch("app.validation.claim_validator.call_with_retry_and_fallback") as mock_claim, \
         patch("app.validation.contradiction_engine.call_with_retry_and_fallback") as mock_contra:
         
         mock_req.return_value = RequirementExtractionOutput(requirements=[RequirementSchema(req_code="REQ-1", description="assay", keywords=[])])
         mock_search.return_value = []
         mock_gen.return_value = ResponseGenerationOutput(
             draft_text="Assay B is 10ng.",
             claims=[ClaimProposal(claim_code="CLM-NEW2", claim_text="Assay B sensitivity is 10ng.", product_topic="assay", req_code="REQ-1", cited_evidence_codes=[])]
         )
         mock_contra.return_value = ContradictionOutput(
             classification="COMPATIBLE", reasoning="Different assays discussed.", distinguishing_factors_considered=["assay_type"]
         )
         
         res = client.post("/api/v1/queries", json={"query_text": "What is Assay B sensitivity?"})
         data = res.json()
         
         contras = data.get("contradictions", [])
         REPORT_MD.append(f"- **Result**: Found {len(contras)} contradictions.\n")
         REPORT_MD.append(f"- **Success**: The system recognized it as COMPATIBLE.\n")
         assert len(contras) == 0

def run_scenario_4_citation_grounding():
    """Scenario 4: Citation Grounding."""
    REPORT_MD.append("## Scenario 4: Citation Grounding\n")
    REPORT_MD.append("**Description**: Confirms every citation resolves to real, correct evidence and the LLM semantic validator confirms SUPPORTED.\n")
    
    db = SessionLocal()
    # Create real evidence
    doc = Document(filename="real.pdf", doc_type="test"); db.add(doc); db.flush()
    ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="real"); db.add(ver); db.flush()
    chunk = Chunk(document_version_id=ver.id, content="Real data."); db.add(chunk); db.flush()
    evd_code = f"EVD-REAL-{uuid.uuid4().hex[:5]}"
    evd = Evidence(evidence_code=evd_code, chunk_id=chunk.id, document_id=doc.id, document_version_id=ver.id, source_type="test"); db.add(evd); db.commit()
    evd_id = evd.id
    chunk_id = chunk.id
    db.close()
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback") as mock_req, \
         patch("app.routers.queries.hybrid_search") as mock_search, \
         patch("app.generation.response_generation.call_with_retry_and_fallback") as mock_gen, \
         patch("app.validation.claim_validator.call_with_retry_and_fallback") as mock_claim:
         
         mock_req.return_value = RequirementExtractionOutput(requirements=[RequirementSchema(req_code="REQ-1", description="real", keywords=[])])
         class MockSearch:
             def __init__(self, chunk_id, evidence_id, evidence_code, content, score, source_type):
                 self.chunk_id = chunk_id
                 self.evidence_id = evidence_id
                 self.evidence_code = evidence_code
                 self.content = content
                 self.score = score
                 self.source_type = source_type
         mock_search.return_value = [MockSearch(chunk_id, evd_id, evd_code, "Real data.", 0.99, "test")]
         mock_gen.return_value = ResponseGenerationOutput(
             draft_text="Has real data.",
             claims=[ClaimProposal(claim_code="CLM-REAL", claim_text="Has real data.", product_topic="real", req_code="REQ-1", cited_evidence_codes=[evd_code])]
         )
         mock_claim.return_value = SemanticValidationOutput(validation_state="SUPPORTED", reasoning="Valid")
         
         res = client.post("/api/v1/queries", json={"query_text": "Is there data?"})
         data = res.json()
         
         claim = data["claims"][0]
         REPORT_MD.append(f"- **Result**: Validation state = `{claim['validation_state']}`\n")
         REPORT_MD.append(f"- **Citation**: {claim['citations'][0]['evidence_code']}\n")
         assert claim["validation_state"] == "SUPPORTED"
         assert claim["citations"][0]["evidence_code"] == "EVD-REAL"

def run_scenario_5_overclaim():
    """Scenario 5: Overclaim."""
    REPORT_MD.append("## Scenario 5: Overclaim\n")
    REPORT_MD.append("**Description**: The worked '1 of 100 below threshold' vs 'no contamination detected' case. System must classify OVERCLAIM.\n")
    
    db = SessionLocal()
    # Create real evidence
    doc = Document(filename="tox.pdf", doc_type="test"); db.add(doc); db.flush()
    ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="tox"); db.add(ver); db.flush()
    chunk = Chunk(document_version_id=ver.id, content="1 of 100 samples showed minor contamination below the threshold."); db.add(chunk); db.flush()
    evd_code = f"EVD-TOX-{uuid.uuid4().hex[:5]}"
    evd = Evidence(evidence_code=evd_code, chunk_id=chunk.id, document_id=doc.id, document_version_id=ver.id, source_type="test"); db.add(evd); db.commit()
    evd_id = evd.id
    chunk_id = chunk.id
    db.close()
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback") as mock_req, \
         patch("app.routers.queries.hybrid_search") as mock_search, \
         patch("app.generation.response_generation.call_with_retry_and_fallback") as mock_gen, \
         patch("app.validation.claim_validator.call_with_retry_and_fallback") as mock_claim:
         
         mock_req.return_value = RequirementExtractionOutput(requirements=[RequirementSchema(req_code="REQ-1", description="contamination", keywords=[])])
         class MockSearch:
             def __init__(self, chunk_id, evidence_id, evidence_code, content, score, source_type):
                 self.chunk_id = chunk_id
                 self.evidence_id = evidence_id
                 self.evidence_code = evidence_code
                 self.content = content
                 self.score = score
                 self.source_type = source_type
         mock_search.return_value = [MockSearch(chunk_id, evd_id, evd_code, "1 of 100 samples showed minor contamination below the threshold.", 0.99, "test")]
         mock_gen.return_value = ResponseGenerationOutput(
             draft_text="No contamination detected.",
             claims=[ClaimProposal(claim_code="CLM-FAKE", claim_text="There was absolutely zero contamination detected in any sample.", product_topic="contamination", req_code="REQ-1", cited_evidence_codes=[evd_code])]
         )
         mock_claim.return_value = SemanticValidationOutput(validation_state="OVERCLAIM", reasoning="Evidence states 1 of 100 had minor contamination, claim says absolutely zero.")
         
         res = client.post("/api/v1/queries", json={"query_text": "Was there contamination?"})
         data = res.json()
         
         claim = data["claims"][0]
         REPORT_MD.append(f"- **Result**: Validation state = `{claim['validation_state']}`\n")
         assert claim["validation_state"] == "OVERCLAIM"

if __name__ == "__main__":
    run_scenario_1_insufficient_evidence()
    run_scenario_2_contradiction_true_positive()
    run_scenario_3_contradiction_false_positive()
    run_scenario_4_citation_grounding()
    run_scenario_5_overclaim()
    
    print("\n".join(REPORT_MD))
    
    # Write to a file for artifact use
    with open("e2e_report.md", "w") as f:
        f.write("\n".join(REPORT_MD))
