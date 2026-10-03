# ReguLens: Regulator Demo Queries (`paper4.pdf`, `paper5.pdf`, `paper6.pdf`)

This file provides **5 curated regulator queries** tailored specifically to the payload of **`paper4.pdf`** (*Scaffold Biomaterials in Cultured Meat*), **`paper5.pdf`** (*CMSI Culture Medium Safety*), and **`paper6.pdf`** (*Establishing Food-Safe Cell Lines and Banks*).

Use these exact prompts during your live demo to showcase every possible outcome of the ReguLens pipeline: **Full Sufficiency**, **Partial Evidence / Gap Detection**, and **Total Refusal (Zero Hallucination)**.

---

## Reference Payload Summary
* **`paper4.pdf` (Scaffold Biomaterials):** Animal-derived scaffold biomaterials (`chitosan`, `collagen`, `gelatin`, `fibrin`), GRAS status of chitosan, biocompatibility vs. structural/mechanical limitations, and environmental impact of cultured meat.
* **`paper5.pdf` (Culture Medium Safety):** Transition from fetal bovine serum (FBS) to serum-free media containing recombinant growth factors, medium residues in harvested cell biomass, lack of standardized Certificates of Analysis (CoAs), and analytical method gaps.
* **`paper6.pdf` (Cell Lines & Banking):** Hierarchical cell banking using Master Cell Banks (MCBs) and Working Cell Banks (WCBs), critical control points (adventitious agents, genomic instability, tumorigenicity), immortalized cell line monitoring, and identity verification via cytochrome oxidase I (`COI`) sequencing and PCR genotyping.

---

## Category 1: Completely Sufficient Queries (2 Questions)
*Expected Outcome: **`SUFFICIENT`** badge (Green). Every extracted requirement is backed by `[SUPPORTED]` claims and clickable `[EVD-xxxxx]` PDF citations.*

### Query 1 — Cell Banking & Identity Verification (`paper6.pdf`)
> **"Explain how Master Cell Banks (MCBs) and Working Cell Banks (WCBs) are used to ensure manufacturing consistency in cultivated meat, and identify the molecular methods used to verify cell line species identity and monitor hazards like genomic instability."**

* **Why it works:** Hits exact terminology in `paper6.pdf` (pages 1–2).
* **What it retrieves:**
  * Hierarchical banking structure (MCB as primary characterized repository, WCB as standardized production stock).
  * Hazard control points (microbial contamination, adventitious agents, genomic instability, tumorigenic transformation).
  * Molecular identity markers: cytochrome oxidase I (`COI`) sequencing and PCR-based genotyping.

### Query 2 — Scaffold Biomaterials & Culture Media Safety (`paper4.pdf` + `paper5.pdf`)
> **"Compare the properties and limitations of animal-derived scaffold biomaterials such as chitosan, collagen, and gelatin in cultured meat, and describe the safety challenges associated with serum-free culture media residues and Certificates of Analysis (CoAs)."**

* **Why it works:** Cross-document query spanning both `paper4.pdf` (page 3) and `paper5.pdf` (page 2).
* **What it retrieves:**
  * Chitosan (GRAS status, biocompatible, needs crosslinking/structural reinforcement), Collagen (cell adhesion, lacks mechanical strength), Gelatin (low melting point limits gel formation), Fibrin (high cost).
  * Serum-free media formulations using recombinant proteins/growth factors instead of FBS, residual medium components in final cell biomass, and lack of standardized CoAs from suppliers.

---

## Category 2: Partly Irrelevant Queries (2 Questions)
*Expected Outcome: **`INSUFFICIENT_EVIDENCE`** badge (Red/Amber). The system will generate **`[SUPPORTED]`** claims with citations for the first half of the prompt, but will explicitly flag the second half as unsupported/missing evidence rather than hallucinating an answer.*

### Query 3 — Cell Line Immortalization (Valid) + Human Phase III Cardiac Trials (Irrelevant)
> **"What are the regulatory and biosafety considerations regarding genomic stability and tumorigenicity in immortalized cultivated meat cell lines, and what were the patient arrhythmia rates reported in the 2024 Phase III human clinical cardiovascular trials?"**

* **Why it works for the demo:**
  * **Part 1 (In `paper6.pdf`):** Immortalized cell lines, genomic stability monitoring, and tumorigenic potential are thoroughly covered on page 2 of `paper6.pdf`.
  * **Part 2 (Irrelevant):** Cultivated meat dossiers do not involve Phase III human cardiac arrhythmia trials.
* **What to point out to judges:** Show how the Requirement Extractor splits this into two distinct requirements. Requirement 1 gets answered with verifiable citations from `paper6.pdf`, while Requirement 2 triggers the **Sufficiency Engine** to mark the overall draft `INSUFFICIENT_EVIDENCE` because the clinical trial data does not exist in the vault.

### Query 4 — Culture Media Residues (Valid) + Cold-Chain Lithium Battery Shipping Tariffs (Irrelevant)
> **"Describe the safety risks of culture medium residues remaining in harvested cultivated meat biomass, and provide the European Union customs tariff schedules for lithium-ion battery cold-chain freight containers."**

* **Why it works for the demo:**
  * **Part 1 (In `paper5.pdf`):** Culture medium removal during cell harvest and residual growth factors/components remaining in the final biomass are directly covered on page 2 of `paper5.pdf`.
  * **Part 2 (Irrelevant):** EU customs tariffs and lithium-ion freight regulations are completely absent from the scientific papers.
* **What to point out to judges:** Demonstrates that an attacker or careless writer cannot sneak an unverified regulatory claim into a valid scientific paragraph—ReguLens isolates the missing requirement and blocks full sufficiency approval.

---

## Category 3: Absolutely Irrelevant Query (1 Question)
*Expected Outcome: **`INSUFFICIENT_EVIDENCE`** (Red) with zero fabricated claims. Proves the Cross-Encoder floor (`0.15`) and abstention guardrails work.*

### Query 5 — Completely Out-of-Domain Regulatory Query
> **"Provide the FDA 510(k) electromagnetic compatibility test results and titanium alloy fatigue limits for implantable cardiac pacemakers."**

* **Why it works for the demo:** None of the PDFs in the corpus (`paper4.pdf`, `paper5.pdf`, `paper6.pdf`, or any other cultivated meat paper) mention cardiac pacemakers, 510(k) medical device clearances, or titanium fatigue limits.
* **What happens under the hood:**
  1. Hybrid Search (BM25 + Vector) finds no strong matches.
  2. The `ms-marco-MiniLM` Cross-Encoder scores all candidate chunks below the `0.15` sigmoid relevance threshold, or the LLM abstains due to zero supporting evidence.
  3. The system returns `INSUFFICIENT_EVIDENCE` and refuses to fabricate pacemaker safety data.
