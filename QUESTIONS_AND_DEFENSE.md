# ReguLens: Demo Q&A and Defense Cheat Sheet

This document contains defensive answers for the hardest technical and product questions judges or stakeholders might ask during your demonstration. Keep this open as a reference.

---

## 1. AI Safety & Hallucinations

**Q: How do you guarantee the AI isn't just hallucinating numbers or facts?**
**A:** We don't trust the AI. We built ReguLens on a principle of "Zero-Trust RAG." We enforce two strict guardrails:
1. **Lineage Tracking:** The model is constrained via prompting to output structured JSON claims mapped exactly to `chunk_ids`. If it can't cite the exact paragraph in the database, it is not allowed to generate the claim.
2. **Adversarial Validation Gate:** Before a human even sees the draft, an independent secondary LLM agent (the Sufficiency Engine) cross-references the draft's claims against our historical database to explicitly hunt for contradictions. 

**Q: Why not just use ChatGPT or Claude directly?**
**A:** General-purpose chatbots lack traceability. A regulatory writer cannot submit a dossier to the FDA based on a chatbot's word. ReguLens gives them the exact page number of the source PDF (via our UI citation chips) so they can verify the source data with their own eyes in seconds.

---

## 2. Architecture & Retrieval Strategy

**Q: Why did you use Hybrid Search instead of just a standard Vector Database?**
**A:** Vector search (semantic search) is excellent for understanding *concepts*, but it historically fails at exact keyword matching—which is critical in regulatory documents (e.g., finding exact ISO codes, trial IDs, or chemical names). We use BM25 for sparse keyword matching and Vector search for dense semantic matching, then fuse them together mathematically using Reciprocal Rank Fusion (RRF) to get the best of both worlds.

**Q: What is a "Cross-Encoder" and why did you add it?**
**A:** Basic vector search (bi-encoders) compares documents very quickly, but lacks deep contextual understanding. We use a standard vector search to get the top 50 results, but then we pass those results through a Cross-Encoder (`ms-marco-MiniLM`). The cross-encoder reads the query and the document *simultaneously*, scoring their relevance. We applied a Sigmoid activation function to force these scores between 0 and 1, allowing us to implement a strict, mathematical cut-off floor (0.15). Anything below that is thrown out as garbage.

**Q: How do you handle bad PDFs (like scanned images)?**
**A:** Our ingestion pipeline uses layout-aware parsing. If a PDF is a scanned image with no extractable text, the parser detects a zero-byte text return, safely rolls back the database transaction, cleans up the file system, and returns a graceful `UNSUPPORTED_DOCUMENT` error to the UI.

---

## 3. Data Privacy & Security

**Q: Is our highly confidential clinical data being sent to OpenAI or Google for embeddings?**
**A:** Absolutely not. We engineered the ingestion pipeline to use a local embedding model (`all-MiniLM-L6-v2`). When a document is uploaded, the text is chunked and embedded using local CPU/GPU resources. The raw data never leaves the internal VPC during the vectorization phase. 

**Q: Are the PDFs secure when served to the frontend?**
**A:** Yes. The `GET /api/v1/documents/{id}/pdf` endpoint is protected against Path Traversal attacks. It does not accept arbitrary file paths. It takes a UUID, verifies authorization via Bearer token, looks up the verified file path in Postgres, and only serves the exact matching document.

---

## 4. Performance & Scalability

**Q: Large language models have strict rate limits. How did you handle that?**
**A:** We ran into severe Tokens-Per-Minute (TPM) limits early on, specifically the 8,000 TPM limit on Groq's 120b model. We engineered a robust workaround:
1. We dynamically truncate retrieved evidence chunks to 900 characters each.
2. We strictly cap the context window to the top 3-5 chunks.
3. We explicitly manage the `max_tokens` parameter in the API call so the provider doesn't preemptively reserve the maximum context window block. This brought our pipeline latency down from timeouts to just a few seconds.

**Q: Why did you use Postgres instead of a dedicated vector database like Pinecone?**
**A:** We use Postgres with the `pgvector` extension. In enterprise environments, minimizing infrastructure sprawl is critical. By keeping our relational data (document metadata, versioning, audit logs) and our vector embeddings in the same ACID-compliant database, we guarantee that if a document is deleted or rolled back, its vectors are immediately deleted too. No ghost data.

---

## 5. The Future / Next Steps

**Q: If you had another month, what would you add?**
**A:** Three things:
1. **Multi-modal parsing:** Upgrading the parser to extract and embed tables and charts, not just raw text.
2. **Local LLM integration:** Swapping out the API call for a locally hosted LLaMA-3 instance to make the entire system 100% air-gapped for maximum security.
3. **Automated FDA Formatting:** Exporting the approved draft directly into the exact eCTD (Electronic Common Technical Document) XML structure required by health authorities.
