import type { Document, Evidence, Response, Query } from '../types';

export const mockDocuments: Document[] = [
  {
    id: 'doc-001',
    title: 'Microbiological Safety Assessment',
    type: 'Internal Study',
    jurisdiction: 'India',
    currentVersion: 3,
    status: 'READY',
    uploadedAt: 'Sep 29, 2026',
    versions: [
      { version: 3, status: 'CURRENT',    uploadedAt: 'Sep 29, 2026', chunkCount: 42 },
      { version: 2, status: 'SUPERSEDED', uploadedAt: 'Sep 20, 2026', chunkCount: 38 },
      { version: 1, status: 'SUPERSEDED', uploadedAt: 'Sep 11, 2026', chunkCount: 35 },
    ],
  },
  {
    id: 'doc-002',
    title: 'Manufacturing Controls Report',
    type: 'Internal Study',
    jurisdiction: 'India',
    currentVersion: 2,
    status: 'READY',
    uploadedAt: 'Sep 20, 2026',
    versions: [
      { version: 2, status: 'CURRENT',    uploadedAt: 'Sep 20, 2026', chunkCount: 28 },
      { version: 1, status: 'SUPERSEDED', uploadedAt: 'Sep 11, 2026', chunkCount: 25 },
    ],
  },
  {
    id: 'doc-003',
    title: 'Novel Food Safety Review',
    type: 'Scientific Paper',
    jurisdiction: 'India',
    currentVersion: 1,
    status: 'READY',
    uploadedAt: 'Sep 15, 2026',
    versions: [
      { version: 1, status: 'CURRENT', uploadedAt: 'Sep 15, 2026', chunkCount: 61 },
    ],
  },
  {
    id: 'doc-004',
    title: 'Previous Regulator Response',
    type: 'Prior Response',
    jurisdiction: 'India',
    currentVersion: 4,
    status: 'APPROVED',
    uploadedAt: 'Sep 10, 2026',
    versions: [
      { version: 4, status: 'CURRENT',    uploadedAt: 'Sep 10, 2026', chunkCount: 15 },
      { version: 3, status: 'SUPERSEDED', uploadedAt: 'Sep 01, 2026', chunkCount: 14 },
      { version: 2, status: 'SUPERSEDED', uploadedAt: 'Aug 22, 2026', chunkCount: 12 },
      { version: 1, status: 'SUPERSEDED', uploadedAt: 'Aug 10, 2026', chunkCount: 10 },
    ],
  },
  {
    id: 'doc-005',
    title: 'Contaminant Screening Protocol',
    type: 'Internal Study',
    jurisdiction: 'India',
    currentVersion: 1,
    status: 'PROCESSING',
    uploadedAt: 'Sep 29, 2026',
    versions: [
      { version: 1, status: 'CURRENT', uploadedAt: 'Sep 29, 2026', chunkCount: 0 },
    ],
  },
];

export const mockEvidenceMap: Record<string, Evidence> = {
  'EVD-01872': {
    id: 'evd-001',
    code: 'EVD-01872',
    documentTitle: 'Microbiological Safety Assessment',
    documentVersion: 3,
    page: 17,
    section: '4.2',
    sourceType: 'Internal Study',
    excerpt:
      'No detectable microbial contamination was observed above the assay reporting threshold across the tested production batches. All batch results were within the defined acceptance criteria for Salmonella spp., E. coli O157:H7, Listeria monocytogenes, and total aerobic count.',
  },
  'EVD-01208': {
    id: 'evd-002',
    code: 'EVD-01208',
    documentTitle: 'Manufacturing Controls Report',
    documentVersion: 2,
    page: 8,
    section: '3.1',
    sourceType: 'Internal Study',
    excerpt:
      'The production process incorporates defined microbiological controls at each critical control point (CCP), including in-process environmental monitoring, end-product testing, and supplier qualification programs aligned with HACCP principles.',
  },
  'EVD-00934': {
    id: 'evd-003',
    code: 'EVD-00934',
    documentTitle: 'Novel Food Safety Review',
    documentVersion: 1,
    page: 4,
    section: '2.1',
    sourceType: 'Scientific Paper',
    excerpt:
      'Cultivated meat products produced under GMP conditions demonstrated comparable or superior microbiological safety profiles to conventional meat products across three independent laboratory validations.',
  },
};

export const DEMO_QUERY =
  'Provide evidence supporting the microbiological safety of the cultivated-cell product and describe the controls used during production.';

export const mockResponse: Response = {
  id: 'resp-001',
  code: 'R-014',
  queryText: DEMO_QUERY,
  draftText:
    'Based on the available microbiological testing data, no detectable microbial contamination was observed above the assay reporting threshold across the tested production batches [EVD-01872]. All batch results met acceptance criteria for Salmonella spp., E. coli O157:H7, Listeria monocytogenes, and total aerobic count.\n\nThe production process incorporates defined microbiological controls at each critical control point, including in-process environmental monitoring, end-product testing, and supplier qualification programs aligned with HACCP principles [EVD-01208]. These controls are documented in the Manufacturing Controls Report (v2) and are subject to periodic internal audit.\n\nIndependent laboratory validation of cultivated cell production under GMP conditions has demonstrated comparable safety profiles to conventional counterparts [EVD-00934].',
  status: 'PENDING_REVIEW',
  claims: [
    {
      id: 'claim-001',
      code: 'CLM-001',
      text: 'No detectable microbial contamination was observed above the assay reporting threshold across the tested production batches.',
      status: 'SUPPORTED',
      citedEvidence: ['EVD-01872'],
    },
    {
      id: 'claim-002',
      code: 'CLM-002',
      text: 'The production process incorporates defined microbiological controls at each critical control point.',
      status: 'SUPPORTED',
      citedEvidence: ['EVD-01208'],
    },
    {
      id: 'claim-003',
      code: 'CLM-003',
      text: 'Independent laboratory validation demonstrated comparable safety profiles to conventional counterparts.',
      status: 'PARTIALLY_SUPPORTED',
      citedEvidence: ['EVD-00934'],
    },
  ],
  requirements: [
    { id: 'req-001', code: 'REQ-01', description: 'Microbiological safety evidence',     coverage: 'COVERED',           evidenceCount: 3 },
    { id: 'req-002', code: 'REQ-02', description: 'Production microbiological controls',  coverage: 'COVERED',           evidenceCount: 2 },
    { id: 'req-003', code: 'REQ-03', description: 'Contaminant testing scope',            coverage: 'PARTIALLY_COVERED', evidenceCount: 1 },
    { id: 'req-004', code: 'REQ-04', description: 'Long-term toxicity data',              coverage: 'NOT_COVERED',       evidenceCount: 0 },
  ],
  contradictions: [
    {
      id: 'cont-001',
      level: 'POTENTIAL_CONTRADICTION',
      newClaim: {
        text: 'No detectable microbial contamination above the reporting threshold.',
        source: 'Microbiological Study S-008',
        date: 'Sep 28, 2026',
      },
      historicalClaim: {
        text: 'No microbial contamination was detected.',
        source: 'Previous Response R-012',
        date: 'Sep 15, 2026',
      },
      factors: ['Reporting threshold', 'Study date', 'Sample scope', 'Testing conditions', 'Document version'],
    },
  ],
  createdAt: '2026-09-29T13:42:00Z',
  auditEvents: [
    { id: 'evt-001', timestamp: '13:42', event: 'Query created',          description: 'Regulatory query submitted for analysis',             actor: 'Akshay R.'  },
    { id: 'evt-002', timestamp: '13:42', event: 'Requirements extracted', description: '4 regulatory requirements identified (LLM Call 1)',    actor: 'System'     },
    { id: 'evt-003', timestamp: '13:43', event: 'Evidence retrieved',     description: '6 evidence items retrieved via hybrid search',         actor: 'System'     },
    { id: 'evt-004', timestamp: '13:43', event: 'Draft generated',        description: 'Response draft generated with 3 claims (LLM Call 2)',  actor: 'System'     },
    { id: 'evt-005', timestamp: '13:43', event: 'Citations validated',    description: 'All 3 citation IDs verified against evidence database', actor: 'System'     },
    { id: 'evt-006', timestamp: '13:44', event: 'Claims validated',       description: '2 SUPPORTED, 1 PARTIALLY_SUPPORTED (LLM Call 3)',      actor: 'System'     },
    { id: 'evt-007', timestamp: '13:44', event: 'Contradiction detected', description: '1 potential contradiction flagged (LLM Call 4)',        actor: 'System'     },
    { id: 'evt-008', timestamp: '13:45', event: 'Human review started',   description: 'Response sent to review queue',                        actor: 'System'     },
  ],
};

export const mockQueries: Query[] = [
  {
    id: 'qry-001',
    text: DEMO_QUERY,
    status: 'COMPLETE',
    createdAt: 'Sep 29, 2026 · 13:42',
    responseId: 'resp-001',
  },
  {
    id: 'qry-002',
    text: 'Describe the manufacturing process validation studies and quality assurance procedures for the cultivated meat product.',
    status: 'PENDING',
    createdAt: 'Sep 28, 2026 · 09:15',
  },
  {
    id: 'qry-003',
    text: 'Provide a risk assessment for the novel food ingredient covering allergenicity, toxicology, and nutritional equivalence.',
    status: 'COMPLETE',
    createdAt: 'Sep 27, 2026 · 11:30',
    responseId: 'resp-002',
  },
];
