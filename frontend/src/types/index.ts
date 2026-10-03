export type DocumentStatus = 'READY' | 'PROCESSING' | 'FAILED' | 'APPROVED';
export type DocumentType = 'Internal Study' | 'Scientific Paper' | 'Prior Response' | 'Regulatory Letter';
export type ClaimStatus = 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'OVERCLAIM' | 'POTENTIAL_CONTRADICTION';
export type RequirementCoverage = 'COVERED' | 'PARTIALLY_COVERED' | 'NOT_COVERED';
export type ResponseStatus = 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED';
export type ContradictionLevel = 'POTENTIAL_CONTRADICTION' | 'LIKELY_CONTRADICTION' | 'COMPATIBLE' | 'INSUFFICIENT_CONTEXT';
export type QueryStatus = 'PENDING' | 'ANALYZING' | 'COMPLETE' | 'FAILED';

export interface DocumentVersion {
  version: number;
  status: 'CURRENT' | 'SUPERSEDED';
  uploadedAt: string;
  chunkCount: number;
}

export interface Document {
  id: string;
  title: string;
  type: DocumentType;
  jurisdiction: string;
  currentVersion: number;
  status: DocumentStatus;
  uploadedAt: string;
  versions: DocumentVersion[];
}

export interface Evidence {
  id: string;
  code: string;
  documentTitle: string;
  documentVersion: number;
  page: number;
  section: string;
  sourceType: string;
  excerpt: string;
}

export interface Requirement {
  id: string;
  code: string;
  description: string;
  coverage: RequirementCoverage;
  evidenceCount: number;
}

export interface Claim {
  id: string;
  code: string;
  text: string;
  status: ClaimStatus;
  citedEvidence: string[];
}

export interface Contradiction {
  id: string;
  level: ContradictionLevel;
  newClaim: { text: string; source: string; date: string };
  historicalClaim: { text: string; source: string; date: string };
  factors: string[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event: string;
  description: string;
  actor?: string;
}

export interface Response {
  id: string;
  code: string;
  queryText: string;
  draftText: string;
  status: ResponseStatus;
  claims: Claim[];
  requirements: Requirement[];
  contradictions: Contradiction[];
  createdAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
  auditEvents: AuditEvent[];
}

export interface Query {
  id: string;
  text: string;
  status: QueryStatus;
  createdAt: string;
  responseId?: string;
}
