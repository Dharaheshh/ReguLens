# ReguLens — Stitch Design & Frontend Specification

> **Purpose:** Master design brief for generating the ReguLens frontend in Stitch.
>
> **Scope:** TASK-019, TASK-020, TASK-021, TASK-022, plus the shared application shell and design system.
>
> **Primary implementation target:** React + TypeScript + Vite frontend.
>
> **Design principle:** Evidence → Requirements → Claims → Citations → Validation → Human Approval.

---

# 1. Product Context

## 1.1 Product

**ReguLens** is an AI-powered regulatory evidence workspace for a cultivated-food / biotechnology company.

It helps regulatory and scientific teams transform regulator questions into **evidence-grounded, auditable draft responses**.

ReguLens is an **internal professional application**.

It is NOT:

- a marketing website
- a consumer application
- a generic AI chatbot
- a futuristic AI command-center dashboard

## 1.2 Primary Users

The primary users are:

- Regulatory affairs professionals
- Food scientists
- Safety researchers
- Scientific reviewers
- Compliance reviewers

## 1.3 Core Product Flow

The product's core conceptual flow is:

```text
Evidence
    ↓
Requirements
    ↓
Claims
    ↓
Citations
    ↓
Validation
    ↓
Human Approval
```

The UI must make this trust model obvious.

The product should visually distinguish:

- AI-generated draft
- retrieved source evidence
- validated claims
- human-approved response

The interface must never imply that AI-generated text is automatically trustworthy.

---

# 2. Visual Brand Direction

## 2.1 Biokraft Inspiration

The product is associated with **Biokraft Foods**, a cultivated-meat / biotechnology company.

Use the general visual character of:

- biotechnology
- cultivated food
- scientific research
- cellular/biological systems
- precision
- evidence
- modern premium technology

as visual inspiration.

### Do NOT copy

Do not copy:

- Biokraft's website layout
- Biokraft's logo
- exact branding
- exact assets
- exact illustrations
- exact website components
- marketing-page structure

Create a distinct **ReguLens** identity.

The result should feel inspired by the same scientific/biotech world, not like a clone of the company's website.

---

# 3. Color Direction

## 3.1 Primary Brand Direction

**Green is the primary ReguLens brand/accent color.**

The green direction is inspired by biotechnology and Biokraft's visual identity.

However:

> **Do not make the entire application green.**

Green should function as a controlled brand accent and semantic signal.

## 3.2 Suggested Visual Hierarchy

Use:

- **Deep biotech green** → primary actions, active navigation
- **Medium/muted green** → secondary accents
- **Very light green** → evidence/citation surfaces
- **White/off-white** → application backgrounds and surfaces
- **Charcoal/near-black** → primary text
- **Soft neutral gray** → borders and metadata
- **Amber** → warnings / caution
- **Red** → errors / destructive actions

## 3.3 Semantic Color Rules

Green should communicate:

- brand identity
- evidence/support
- approved states
- important actions
- supported claims

Amber should communicate:

- caution
- potential contradiction
- human review required

Red should communicate:

- errors
- destructive actions
- rejection

Insufficient evidence must be visually distinct from a technical/application error.

### Important rule

> **Green should tell the user where ReguLens is supported, active, approved, or asking them to act — not simply make the screen green.**

---

# 4. Desired Product Feel

The application should feel:

- scientific
- premium
- trustworthy
- precise
- calm
- modern
- enterprise-grade
- information-dense but uncluttered

Useful visual references include:

- modern scientific software
- Linear
- Notion
- enterprise research tools

Do NOT make the interface:

- generic AI-gradient-heavy
- neon
- cyberpunk
- excessively glassmorphic
- excessively animated
- overloaded with decorative graphics
- excessively rounded/card-heavy
- chatbot-like

The visual hierarchy should prioritize:

```text
Evidence
   >
Claims
   >
Validation
   >
Actions
   >
Decoration
```

---

# 5. Core UX Principles

## 5.1 Evidence First

The application should make evidence easy to inspect and trace.

A reviewer should be able to move from:

```text
Claim
  ↓
Citation
  ↓
Evidence
  ↓
Document
  ↓
Version
  ↓
Page / Section
```

## 5.2 AI Is Not the Source of Truth

The interface must visually distinguish:

```text
AI-generated draft
        ≠
Source evidence
        ≠
Validation result
        ≠
Human approval
```

## 5.3 Human Review Is Mandatory

The final response is not approved automatically.

The system can:

- retrieve evidence
- extract requirements
- draft a response
- extract claims
- propose citations
- validate claims
- identify potential contradictions
- identify evidence gaps

A human must explicitly approve the response.

## 5.4 Potential Contradiction ≠ Confirmed Contradiction

The contradiction UI must communicate:

> "There may be a meaningful difference. I need to inspect the evidence."

It must NOT communicate:

> "The AI has proven these claims are contradictory."

Use **Potential contradiction** and **Human review required**.

## 5.5 Evidence Gap ≠ Technical Error

A requirement with insufficient evidence is a meaningful product state.

It is not an application failure.

The UI should communicate:

> "The system does not have enough evidence to support this conclusion."

It should not fabricate or imply a conclusion.

---

# 6. Application Information Architecture

The main desktop application should use this shell:

```text
┌────────────────────────────────────────────────────────────┐
│ TOP BAR                                                    │
├────────────────┬───────────────────────────────────────────┤
│ SIDEBAR        │ MAIN CONTENT                              │
│                │                                           │
│                │                                           │
└────────────────┴───────────────────────────────────────────┘
```

## Sidebar

Brand:

**ReguLens**

Navigation:

### WORKSPACE

- Overview
- Documents
- Queries
- Reviews

### SYSTEM

- Audit Log
- Settings

The active navigation item must be clearly identifiable.

The sidebar should be understated rather than visually dominant.

Use the green accent primarily for:

- active navigation
- selected states
- primary actions

## Top Bar

Include:

- current workspace/page context
- global search
- notification indicator
- reviewer/user menu

## Main Content

Use consistent:

- page margins
- title hierarchy
- action placement
- spacing
- content width

The content area must provide enough horizontal space for:

- document tables
- evidence
- claims
- citations
- validation results
- review information

The shell must support a desktop-first professional workflow.

---

# 7. Shared Design System

Create reusable definitions for:

1. Colors
2. Typography
3. Spacing
4. Borders
5. Border radius
6. Shadows/elevation
7. Buttons
8. Inputs
9. Selects
10. Tables
11. Cards
12. Status badges
13. Evidence badges
14. Citation chips
15. Drawers
16. Modals
17. Alerts
18. Empty states
19. Loading states
20. Error states

## Typography

Establish clear styles for:

- display
- page title
- section title
- body
- metadata
- labels
- evidence identifiers / code-like values

## Buttons

Support:

- primary
- secondary
- ghost
- destructive
- disabled
- loading

## Form Controls

Support:

- text input
- search
- textarea
- select
- checkbox
- PDF file upload

## Semantic Statuses

Create clear visual language for:

- SUPPORTED
- PARTIALLY_SUPPORTED
- UNSUPPORTED
- OVERCLAIM
- POTENTIAL_CONTRADICTION
- INSUFFICIENT_EVIDENCE
- PROCESSING
- READY
- FAILED
- APPROVED
- REJECTED

The design must make these distinctions obvious.

---

# 8. TASK-019 — Document Library

## Purpose

The Document Library is the central repository for regulatory evidence.

Users can:

- upload PDFs
- search documents
- filter documents
- inspect metadata
- inspect document versions
- see processing status

## Page Header

Title:

**Documents**

Subtitle:

**Regulatory evidence library**

Primary action:

**+ Upload document**

## Search and Filters

Provide:

- Search documents...
- Document type filter
- Jurisdiction filter
- Status filter

## Document List

Use a professional information-dense table.

Columns:

- Document
- Type
- Jurisdiction
- Version
- Status
- Uploaded
- Actions

## Example Synthetic Documents

Use clearly synthetic/example data:

### Microbiological Safety Assessment

- Type: Internal Study
- Jurisdiction: India
- Version: v3
- Status: Ready

### Manufacturing Controls Report

- Type: Internal Study
- Jurisdiction: India
- Version: v2
- Status: Ready

### Novel Food Safety Review

- Type: Scientific Paper
- Jurisdiction: India
- Version: v1
- Status: Ready

### Previous Regulator Response

- Type: Prior Response
- Jurisdiction: India
- Version: v4
- Status: Approved

## Document Row Interaction

Clicking a document opens document details.

Show:

- filename
- document type
- jurisdiction
- current version
- status
- upload date

## Version History

Show:

```text
v3 — Current
v2 — Superseded
v1 — Superseded
```

Each version should display:

- version number
- status
- uploaded date

The current version should be visually distinct using the ReguLens green accent.

Superseded versions must not look deleted. They remain part of the audit history.

## Upload Flow

Create a polished PDF upload experience with:

1. Initial
2. File selected
3. Uploading
4. Processing
5. Successfully processed
6. Failed

During processing, communicate stages such as:

```text
Parsing document
Creating evidence chunks
Generating embeddings
Building evidence records
```

Do not use fake percentage progress.

## Empty State

Explain what the document library is for and provide a clear upload action.

## Error State

Provide:

- useful human-readable message
- retry action

Do not expose internal implementation details.

## Versioning Principle

Documents are versioned.

The UI must never imply that an existing version was silently overwritten.

---

# 9. Document Details + Version History

Create a dedicated document details view.

## Header

Example:

**Microbiological Safety Assessment**

Metadata:

- Internal Study
- India
- Version 3
- Ready

Actions:

- Upload new version
- View document
- More actions

## Document Information

Show:

- filename
- document type
- jurisdiction
- current version
- uploaded date
- processing status

## Version History

Create a clear chronological version timeline/table.

Example:

```text
v3
Current
Sep 29, 2026

v2
Superseded
Sep 20, 2026

v1
Superseded
Sep 11, 2026
```

The current version should use the ReguLens green accent.

Superseded versions remain queryable/auditable and must not look deleted.

---

# 10. TASK-020 — Query Workspace

## Purpose

This is the primary ReguLens demonstration screen.

A regulatory professional enters a regulator question.

ReguLens:

1. extracts requirements
2. retrieves evidence
3. generates a draft
4. extracts claims
5. proposes citations
6. validates claims against cited evidence
7. identifies evidence gaps
8. identifies potential contradictions
9. requires human review

The UI must communicate this workflow clearly without exposing unnecessary technical implementation details.

## Page Header

Title:

**Query Workspace**

Subtitle:

**Build an evidence-grounded response to a regulatory question.**

## Query Area

Large textarea placeholder:

> Enter the regulator's question...

Primary action:

**Run analysis**

Query states:

- Ready
- Analyzing
- Complete
- Failed

## Requirements Section

Display extracted requirements.

Example:

```text
Requirements

✓ Microbiological safety evidence
  3 evidence items

✓ Production microbiological controls
  2 evidence items
```

Show requirement coverage clearly.

## Draft Response Section

Display the generated response in a highly readable, document-like area.

Example:

> Based on the available microbiological testing data, no detectable microbial contamination was observed above the assay reporting threshold across the tested production batches...

Inline citations:

```text
[EVD-01872]
[EVD-01208]
```

Citation chips must be visually interactive.

## Claim Validation Section

Display claims extracted from the draft.

Example:

### Claim

No detectable microbial contamination was observed...

### Status

SUPPORTED

### Evidence

EVD-01872

Another example:

### Claim

The production process incorporates defined microbiological controls.

### Status

SUPPORTED

### Evidence

EVD-01208

Support states:

- SUPPORTED
- PARTIALLY SUPPORTED
- UNSUPPORTED
- OVERCLAIM
- POTENTIAL CONTRADICTION

## Evidence Section

Selecting a citation opens the Evidence Detail panel.

Show:

- Evidence ID
- Document
- Version
- Page
- Section
- Source type
- Evidence excerpt

## Insufficient Evidence State

Create a complete example where the system cannot support a requirement.

Example:

### Evidence gap

**Long-term toxicity**

No directly supporting evidence was retrieved.

Related evidence:

- 28-day toxicity study
- Genotoxicity study
- Cell viability study

The UI must clearly communicate:

> The system does not have enough evidence to support this conclusion.

Do not generate an unsupported conclusion.

## Loading State

Show analysis in progress without fake percentage progress.

Use a calm, professional state.

## Error State

Show:

- what failed
- retry action

## Overall Visual Story

The workspace should communicate:

```text
Question
    ↓
Requirements
    ↓
Evidence
    ↓
Draft
    ↓
Claims
    ↓
Validation
    ↓
Human Review
```

---

# 11. Citation + Evidence Interaction

This is a reusable interaction used inside:

- Query Workspace
- Review Workspace
- Draft responses
- Claim validation

## Core Principle

Every important regulatory claim should be traceable to evidence.

Example:

> No detectable microbial contamination was observed above the assay reporting threshold [EVD-01872].

`[EVD-01872]` is an interactive citation chip.

## Citation States

Create:

1. Default
2. Hover
3. Focus
4. Selected
5. Loading
6. Evidence unavailable
7. Invalid citation

## Click Interaction

Clicking a citation opens a right-side Evidence Drawer.

Show:

### Evidence

**EVD-01872**

**Microbiological Safety Assessment**

Version 3

Page 17  
Section 4.2  
Source type: Internal Study

### Evidence Excerpt

> "No detectable microbial contamination was observed above the assay reporting threshold across the tested production batches."

Actions:

- Open document
- Close

## Visual Distinction

The evidence excerpt should visually resemble source material.

The generated claim should visually resemble application-generated content.

They must not look identical.

Use a subtle green accent for the evidence/citation interaction.

Do not overuse green.

The interaction should feel:

- fast
- precise
- trustworthy
- professional

Design this as a reusable component system rather than one static example.

---

# 12. TASK-021A — Contradiction Panel

TASK-021 depends on TASK-020, TASK-016 and TASK-017 for real data.

The UI can be designed and implemented with clearly labelled fixture/mock data before those backend dependencies are available, but real integration must wait for the actual contracts.

## Purpose

This is a human review tool.

The system identifies a **potential contradiction**.

It does NOT automatically decide that two scientific claims are contradictory.

## Header

**Potential contradiction detected**

Status:

**Human review required**

## Side-by-Side Comparison

### New Claim

> "No detectable microbial contamination above the reporting threshold."

Source:

Microbiological Study S-008

Date:

28 Sep 2026

### Historical Claim

> "No microbial contamination was detected."

Source:

Previous Response R-012

Date:

15 Sep 2026

## Distinguishing Factors

Display possible differences:

- Reporting threshold
- Study date
- Sample scope
- Testing conditions
- Document version

## Critical Rule

Do NOT label this:

> Confirmed contradiction

Use:

> Potential contradiction

The user should understand:

> There may be a meaningful difference. I need to inspect the evidence.

## Action

**Review evidence**

## States

Create:

- potential contradiction
- insufficient context
- expanded evidence
- reviewed

Use amber/caution visual language rather than red error styling.

Green remains reserved primarily for:

- supported
- approved
- primary brand actions

---

# 13. TASK-021B — Evidence Gap Map

TASK-021 also contains the evidence gap map.

## Purpose

Show whether each extracted regulatory requirement has supporting evidence.

This represents **requirement coverage**.

It is NOT:

- a safety score
- a scientific confidence score
- a product safety rating

## Header

**Evidence Coverage**

Subtitle:

**Coverage of extracted regulatory requirements based on retrieved evidence.**

## Requirement List

Example:

```text
✓ Microbiological safety
  3 supporting evidence items

✓ Manufacturing controls
  2 supporting evidence items

◐ Contaminant testing
  1 supporting evidence item

! Long-term toxicity
  No directly supporting evidence
```

## States

- COVERED
- PARTIALLY COVERED
- NOT COVERED

For each requirement show:

- requirement text
- coverage state
- evidence count
- expandable evidence

## Not Covered Detail

Example:

### Long-term toxicity

No directly supporting evidence was retrieved.

Related available evidence:

- 28-day toxicity study
- Genotoxicity study
- Cell viability study

Action:

**View related evidence**

## Interactions

Support:

- filter by status
- expand/collapse
- view evidence
- inspect requirement

This should be a prominent panel because evidence gaps are one of the major ReguLens demonstration moments.

Do not use a generic percentage score as the primary representation.

---

# 14. TASK-022 — Human Review Workspace

TASK-022 depends on TASK-018 and TASK-020.

The UI can be designed and implemented against fixture/mock data if the real backend dependency is not yet available. Real integration must wait for the backend contract.

## Purpose

This is the final human control point before a regulatory response becomes approved.

The AI can:

- retrieve evidence
- generate a draft
- propose claims
- propose citations
- validate claims
- identify potential contradictions
- identify evidence gaps

The AI cannot approve the response.

A human must explicitly approve it.

## Header

**Review Response**

Response ID:

**R-014**

Status:

**Awaiting human approval**

## Draft Response

Display the complete response.

Show inline citation chips.

## Claim Validation

Display claims and validation states.

Example:

### SUPPORTED

No detectable microbial contamination was observed...

Evidence:

EVD-01872

Another:

### SUPPORTED

Production controls are defined...

Evidence:

EVD-01208

Warning states must be prominent.

## Review Warnings

If applicable:

- Potential contradiction detected
- Evidence gap detected
- Unsupported claim detected

Warnings must never be hidden.

## Audit Trail

Display chronological events:

```text
13:42
Query created

13:42
Requirements extracted

13:43
Evidence retrieved

13:43
Draft generated

13:43
Claims validated

13:45
Human review started
```

Each event shows:

- timestamp
- event
- description

## Actions

Primary:

**Approve Response**

Secondary:

**Edit Response**

Destructive:

**Reject**

## Approval Confirmation

After approval:

```text
Response approved

Audit event recorded

Approved at:
13:47
```

The approval action must feel deliberate.

Do not design automatic approval.

## States

Create:

- pending review
- editing
- validation warnings
- approval confirmation
- rejection

---

# 15. Synthetic Fixture Data

All example evidence and response data in the design should be clearly understood as synthetic/demo data.

Useful fixtures:

## Evidence

```text
EVD-01872
Microbiological Safety Assessment v3
Page 17
Section 4.2

"No detectable microbial contamination was observed above the assay reporting threshold across the tested production batches."
```

```text
EVD-01208
Manufacturing Controls Report
Section 3.1
```

## Claims

```text
No detectable microbial contamination was observed...
→ SUPPORTED
→ EVD-01872
```

```text
The production process incorporates defined microbiological controls.
→ SUPPORTED
→ EVD-01208
```

## Contradiction Fixture

New:

```text
"No detectable microbial contamination above the reporting threshold."
Study S-008
28 Sep 2026
```

Historical:

```text
"No microbial contamination was detected."
Previous Response R-012
15 Sep 2026
```

Distinguishing factors:

- reporting threshold
- study date
- sample scope
- testing conditions
- document version

## Evidence Gap Fixture

Requirement:

```text
Long-term toxicity
```

Available related evidence:

- 28-day toxicity study
- Genotoxicity study
- Cell viability study

State:

```text
NOT COVERED
```

Do not fabricate actual regulatory conclusions.

---

# 16. Accessibility + UX Quality

All screens should be designed for professional daily use.

Prioritize:

- readable typography
- accessible contrast
- keyboard focus states
- clear interactive states
- meaningful status labels
- predictable navigation
- sufficient whitespace
- clear hierarchy
- responsive desktop behavior

Do not rely on color alone to communicate status.

For example:

SUPPORTED should include:

- semantic label
- icon/indicator where appropriate
- color

not only green.

---

# 17. Responsive Strategy

ReguLens is primarily desktop-first because the target users are regulatory/scientific professionals working with dense evidence.

However, components should degrade gracefully.

Desktop is the primary design target.

Important multi-column areas such as:

- Query Workspace
- Contradiction comparison
- Evidence panels

should remain readable when the viewport becomes narrower.

Avoid designing mobile layouts that destroy the evidence hierarchy.

---

# 18. Global Consistency Rules

Across every screen:

### Use green consistently

Green = brand/support/approved/action.

### Use amber consistently

Amber = caution/potential contradiction/human attention.

### Use red consistently

Red = error/rejection/destructive action.

### Keep evidence visually prominent

Evidence is more important than decorative UI.

### Keep AI output visually distinguishable

Draft ≠ source evidence.

### Keep human approval visually explicit

Approved responses must have a clear human-review boundary.

### Preserve document history

Superseded versions remain visible as historical records.

### Avoid generic AI UX

Do not turn ReguLens into a chat interface.

---

# 19. Required Screens / Components

The complete design should cover:

## Application

- Application Shell
- Sidebar
- Top Bar
- Navigation states
- Overview

## TASK-019

- Document Library
- Document table/list
- Upload flow
- Processing state
- Empty state
- Error state
- Document Details
- Version History

## TASK-020

- Query Workspace
- Query input
- Requirements
- Draft response
- Claim list
- Validation states
- Citation chips
- Evidence drawer
- Insufficient evidence state
- Loading state
- Error state

## TASK-021

- Contradiction Panel
- Gap Map
- Fixture states
- Human review states

## TASK-022

- Review Workspace
- Claim validation
- Warning section
- Approve/Edit/Reject controls
- Audit Trail
- Approval confirmation
- Rejection state

---

# 20. Product-Wide UX Pass

After designing all screens, perform a product-wide consistency pass.

Review:

1. Navigation consistency
2. Typography consistency
3. Green brand color consistency
4. Status semantics
5. Button hierarchy
6. Spacing
7. Tables
8. Forms
9. Evidence/citation interactions
10. Loading states
11. Empty states
12. Error states
13. Responsive behavior
14. Accessibility
15. Visual hierarchy

ReguLens must feel like **one coherent professional application**, not a collection of unrelated screens.

Do not redesign individual screens unnecessarily during the final pass. Preserve strong existing decisions and correct only genuine inconsistencies.

The entire product should consistently communicate:

```text
Evidence
    ↓
Claim
    ↓
Citation
    ↓
Validation
    ↓
Human Approval
```

---

# 21. Task / Dependency Boundaries

## TASK-019

Status for current frontend work:

- Design: can proceed
- Mock implementation: can proceed
- Real backend integration: depends on TASK-008

## TASK-020

Status:

- Design: can proceed
- Mock implementation: can proceed
- Real backend integration: can proceed once query API is available

## TASK-021

Dependencies:

- TASK-020
- TASK-016
- TASK-017

Design can proceed now.

Fixture/mock implementation can proceed if isolated from real backend integration.

Do not claim real integration is complete until those backend contracts exist.

## TASK-022

Dependencies:

- TASK-018
- TASK-020

Design can proceed now.

Fixture/mock implementation can proceed if isolated from real backend integration.

Do not claim real integration is complete until those backend contracts exist.

---

# 22. Stitch Generation Strategy

Generate the product as a **single coherent design system**, not as unrelated individual pages.

Recommended conceptual order:

```text
1. Design System
        ↓
2. Application Shell
        ↓
3. Overview
        ↓
4. Document Library
        ↓
5. Document Details
        ↓
6. Query Workspace
        ↓
7. Citation + Evidence Drawer
        ↓
8. Contradiction Panel
        ↓
9. Gap Map
        ↓
10. Review Workspace
        ↓
11. Product-wide consistency pass
```

The final design should be implementation-ready for a React + TypeScript application.

---

# 23. Master Instruction to Stitch

Read this entire design brief before generating the design.

Do not treat each section as an isolated prompt.

First establish the ReguLens design system and visual language.

Then create the complete application as one cohesive enterprise product.

Prioritize:

1. Trust
2. Evidence visibility
3. Auditability
4. Human control
5. Clear information hierarchy
6. Scientific/biotech visual identity
7. Professional usability

Use the Biokraft-inspired green direction carefully.

Do not clone Biokraft.

Do not make ReguLens look like a generic AI chatbot.

Do not make it look like a marketing website.

Do not use fake AI confidence scores.

Do not imply automatic scientific conclusions.

Do not hide warnings or evidence gaps.

Do not make potential contradictions appear confirmed.

Do not make insufficient evidence look like a technical failure.

Do not make AI-generated drafts look identical to source evidence.

Create a polished, production-quality, desktop-first enterprise regulatory workspace.

The final visual experience should make the following story immediately understandable to a user or hackathon judge:

> A regulator asks a question.
>
> ReguLens extracts what must be answered.
>
> It finds relevant evidence.
>
> It drafts a response.
>
> It breaks the response into claims.
>
> It connects claims to citations.
>
> It validates those claims against the evidence.
>
> It highlights evidence gaps and potential contradictions.
>
> A human reviews the result.
>
> Only then is the response approved.

The design should make that workflow visually obvious without requiring the user to understand the underlying implementation.
