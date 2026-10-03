# ReguLens: Natural Language Pitch Script (How to Explain Our RAG Pipeline to Judges)

Use this script to explain your architecture naturally and conversationally on stage. It walks through the exact problem, how documents enter the system, and the 7-step flow that happens every time a regulator asks a question.

---

## 1. The Opening Hook: Why Normal RAG Fails Here
**What to say:**
> "When a regulatory agency like the FDA or FSSAI sends a dossier query, a company can't just throw their PDFs into ChatGPT or a standard RAG chatbot. Standard RAG is built to be 'helpful'—if you ask it a two-part question and your documents only cover the first part, a normal RAG system will quietly blend loosely related text to guess the second part. In regulatory affairs, an AI guessing or exaggerating isn't a minor bug—it's a compliance failure that gets your product rejected.
>
> So with **ReguLens**, we didn't build a chatbot. We built an **Evidence-Grounded Sufficiency Engine**. Every time a question enters our system, it goes through two strict pipelines: an **Evidence Lineage Ingestion Pipeline** and a **7-Stage Verification Pipeline** that knows how to mathematically prove every sentence—or refuse to answer when the evidence isn't there."

---

## 2. Pipeline 1: How Documents Become "Auditable Evidence" (Ingestion Flow)
**What to say:**
> "Before we ever answer a question, we have to turn raw scientific PDFs into structured, traceable legal evidence. Here is what happens the moment you upload a PDF into ReguLens:
>
> 1. **Versioned Gatekeeping:** First, our parser reads the PDF page by page. If someone uploads a blurry scanned image with no extractable text, our gatekeeper immediately rejects it rather than letting bad data enter the vault. And if you upload a newer version of an existing study, ReguLens automatically marks the old version as *superseded* so the AI never cites outdated science.
> 2. **Section-Aware Chunking:** Instead of blindly chopping text every 500 words and cutting sentences in half, our chunker reads the document's actual section headings—like *Introduction*, *Methodology*, or *Pathogen Screening*. It keeps paragraphs intact and records the exact page numbers and section titles for every single chunk.
> 3. **Dual Indexing (Meaning + Exact Keywords):** Next, we index every chunk in two ways inside PostgreSQL. First, we run a local embedding model (`all-MiniLM-L6-v2`) to store 384-dimensional vectors for conceptual meaning. Second, we build a full-text keyword index (`tsvector`). Why both? Because vector search understands general concepts like *'microbial safety'*, while keyword search catches exact strain codes like *'E. coli O157:H7'*.
> 4. **Minting Immutable Evidence IDs:** Finally, every chunk is assigned a permanent, human-readable Evidence ID—like `EVD-00001`. Our AI is never allowed to cite vague document names; it can only cite these exact `EVD` codes."

---

## 3. Pipeline 2: What Happens When You Run a Query (The 7-Stage Flow)
**What to say:**
> "Now, here is the real magic of ReguLens. When a user pastes a complex regulator question and clicks **Run Analysis**, we don't just search the whole paragraph at once. Instead, our backend runs a 7-stage pipeline:"

### Step 1: Breaking the Question Apart (Requirement Extraction)
> "Regulators almost always ask multi-part questions—for example, asking about *cell bank identity testing* AND *manufacturing passage limits* in the same sentence. If you search that whole sentence at once, the dominant topic drowns out the second one. So **Step 1** uses an LLM call to decompose the prompt into separate, atomic requirements—`REQ-01`, `REQ-02`, and so on—each with its own search keywords."

### Step 2: Three-Layer Hybrid Search & Neural Reranking
> "In **Step 2**, we search our database independently for *each* requirement using three filters:
> * First, we grab the top 20 keyword matches and the top 20 vector similarity matches.
> * Second, we merge them using **Reciprocal Rank Fusion (RRF)**, which boosts chunks that scored well in *both* keyword and semantic search.
> * Third—and this is critical—vector search alone always returns *something*, even if it's garbage. So we pass the top 20 candidates through a **Cross-Encoder neural reranker** (`ms-marco-MiniLM`). The Cross-Encoder reads the requirement and the document chunk side by side and gives it a strict relevance score from 0 to 1. Any chunk scoring below **0.15** is ruthlessly thrown away."

### Step 3: The Hard Evidence Gate (Zero-Hallucination Short-Circuit)
> "In **Step 3**, before we even allow the AI to start writing, we check what survived Step 2. If someone asks an irrelevant question—like asking for *cardiac pacemaker test results* when our vault only has *cultivated meat papers*—zero chunks survive the 0.15 cutoff. Our **Evidence Gate** trips immediately, completely skips the drafting AI, and returns a red `INSUFFICIENT` banner. It literally cannot hallucinate because the LLM is never even called."

### Step 4: Constrained Drafting
> "If valid evidence *does* survive, **Step 4** passes those exact `EVD` chunks to our drafting model. The model is locked into a strict schema: it writes the response, breaks its own answer down into individual atomic claims (`CLM-01`, `CLM-02`), and attaches the exact `[EVD-xxxxx]` code it used for every single claim."

### Step 5: Auditing the AI (Citation & Semantic Claim Validation)
> "We still don't trust the AI's first draft. So **Step 5** runs a two-part audit on every sentence the AI just wrote:
> * **First, a Deterministic Database Check:** We verify in PostgreSQL that every `[EVD-xxxxx]` code the AI cited actually exists and was part of the retrieved evidence pack. If the AI made up a citation ID, we strip it immediately.
> * **Second, an Adversarial AI Auditor:** A separate LLM call takes each claim and compares it word-for-word against the raw PDF paragraph it cited. If the PDF says *'tested in 3 batches'* and the AI wrote *'proven safe across all production scales'*, the auditor catches that exaggeration and downgrades the claim from `SUPPORTED` to `PARTIALLY_SUPPORTED`—flagging it as an overclaim."

### Step 6: The Mathematical Sufficiency Engine
> "In **Step 6**, how do we decide if the overall answer is ready for a regulator? We *never* ask the LLM if its own answer is good enough. Instead, our **Sufficiency Engine** calculates coverage mathematically:
> * A requirement is only marked `COVERED` if it has at least 2 strong evidence matches above our high-confidence score threshold.
> * If *every* requirement is covered, the response gets a green **`SUFFICIENT`** status.
> * If even *one* requirement in a multi-part question has zero evidence, the whole response is flagged **`INSUFFICIENT`**, and the system automatically writes a **Gap Summary** telling the user exactly which requirement is missing data."

### Step 7: Historical Contradiction Scanning
> "Finally, in **Step 7**, ReguLens checks institutional memory. It compares the new claims against previously approved regulator responses in the database. If we told a regulator six months ago that *'no contamination was detected'*, and today's draft says *'no contamination was detected above the reporting threshold'*, our Contradiction Engine flags that subtle shift side-by-side so the team can explain the difference before submitting."

---

## 4. How to Walk Through the UI Output on Screen
**What to say while pointing at the screen:**
> "And all seven of those stages come together on a single screen built for a **Human-in-the-Loop**:
> 1. **At the top**, you see the **Sufficiency Banner**. In one glance, green means full coverage, amber means partial gaps, and red means missing evidence. Expanding it shows the exact checklist of requirements (`REQ-01`, `REQ-02`) so you see *what* was answered and *what* failed.
> 2. **In the middle**, you see the **Drafted Response** broken into visual claim blocks. **Green borders** mean verified facts. **Amber borders** mean the AI overclaimed and a human needs to tone it down.
> 3. **Inside each claim**, you have monospace **`[EVD-xxxxx]` chips**. Clicking any chip opens the **Evidence Drawer** on the right, showing the exact PDF name, version number, page, section, and verbatim paragraph.
> 4. **At the bottom**, the **Review Action Bar** is pinned to the screen. AI never gets the final word in ReguLens—a human specialist must explicitly click **Approve**, **Edit**, or **Reject**, which logs an immutable record in our Audit Trail."
