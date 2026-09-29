"""Generate a 3-page test PDF fixture for TASK-005 testing."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymupdf  # PyMuPDF

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixtures")
os.makedirs(FIXTURE_DIR, exist_ok=True)

OUTPUT = os.path.join(FIXTURE_DIR, "sample_3page.pdf")

doc = pymupdf.open()

# Page 1
page1 = doc.new_page()
page1.insert_text(
    (72, 72),
    "1. Introduction\n\n"
    "This document describes the microbiological safety assessment\n"
    "of the cultivated-cell food product produced by Biokraft GmbH.\n"
    "The assessment covers pathogen screening, contamination controls,\n"
    "and quality assurance procedures implemented during production.\n\n"
    "The product undergoes rigorous testing at multiple stages of the\n"
    "manufacturing process to ensure consumer safety and regulatory\n"
    "compliance across international jurisdictions including SFA, EFSA,\n"
    "and FSANZ.",
    fontsize=11,
)

# Page 2
page2 = doc.new_page()
page2.insert_text(
    (72, 72),
    "2. Methodology\n\n"
    "2.1 Pathogen Screening Protocol\n\n"
    "All production batches are screened for the following pathogens:\n"
    "Salmonella spp., Listeria monocytogenes, E. coli O157:H7, and\n"
    "Staphylococcus aureus. Testing is performed using validated PCR\n"
    "methods with a limit of detection of 1 CFU per 25g sample.\n\n"
    "2.2 Environmental Monitoring\n\n"
    "Production facilities maintain ISO Class 7 cleanroom conditions.\n"
    "Environmental swabs are collected from 20 designated sampling\n"
    "points on a weekly basis. Air particulate monitoring is continuous\n"
    "during all production runs.",
    fontsize=11,
)

# Page 3
page3 = doc.new_page()
page3.insert_text(
    (72, 72),
    "3. Results and Discussion\n\n"
    "No detectable microbial contamination was observed above the\n"
    "assay reporting threshold across 847 production batches tested\n"
    "during the 2024-2025 validation period. Environmental monitoring\n"
    "data showed consistent compliance with cleanroom specifications.\n\n"
    "3.1 Statistical Analysis\n\n"
    "The 95% confidence interval for the contamination rate is\n"
    "0.000 to 0.004 events per batch, based on the observed zero\n"
    "contamination events across the full testing period. This meets\n"
    "the acceptance criteria established by the EFSA guidance on\n"
    "novel food safety assessment (EFSA-Q-2023-00456).",
    fontsize=11,
)

doc.save(OUTPUT)
doc.close()
print(f"Created: {OUTPUT}")
