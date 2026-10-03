import { useState, useEffect } from 'react';
import { Upload, Search, Filter, MoreHorizontal, X, FileUp, CheckCircle2, AlertCircle, Loader2, FolderOpen } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { Document } from '../types';

type UploadStep = 'idle' | 'selected' | 'uploading' | 'processing' | 'complete' | 'failed';

const PROCESSING_STAGES = [
  'Parsing document',
  'Creating evidence chunks',
  'Generating embeddings',
  'Building evidence records',
];

const TYPE_COLORS: Record<string, string> = {
  'Internal Study':   'bg-blue-50 text-blue-700',
  'Scientific Paper': 'bg-purple-50 text-purple-700',
  'Prior Response':   'bg-rl-green-50 text-rl-green-700',
  'Regulatory Letter':'bg-rl-amber-50 text-rl-amber-700',
};

function UploadModal({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState<UploadStep>('idle');
  const [fileName, setFileName] = useState('');
  const [processingStage, setProcessingStage] = useState(0);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file: File) => {
    setFileName(file.name);
    setStep('selected');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === 'application/pdf') handleFile(file);
  };

  const runUpload = async () => {
    setStep('uploading');
    await delay(1200);
    setStep('processing');
    for (let i = 0; i < PROCESSING_STAGES.length; i++) {
      setProcessingStage(i);
      await delay(900);
    }
    setStep('complete');
  };

  const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 animate-fade-in px-4">
      <div className="bg-white rounded-rl-lg shadow-rl-lg w-full max-w-md border border-rl-neutral-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-rl-neutral-200">
          <h2 className="text-sm font-semibold text-rl-neutral-900">Upload document</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-rl-neutral-100 text-rl-neutral-500 transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="p-5">
          {(step === 'idle' || step === 'selected') && (
            <>
              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => document.getElementById('file-input')?.click()}
                className={`
                  border-2 border-dashed rounded-rl-md p-8 flex flex-col items-center gap-3 cursor-pointer transition-colors
                  ${dragOver ? 'border-rl-green-400 bg-rl-green-50' : 'border-rl-neutral-200 hover:border-rl-green-300 hover:bg-rl-neutral-50'}
                `}
              >
                <div className="w-10 h-10 rounded-full bg-rl-neutral-100 flex items-center justify-center">
                  <FileUp size={18} className="text-rl-neutral-500" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-rl-neutral-700">
                    {step === 'selected' ? fileName : 'Drop a PDF here, or click to browse'}
                  </p>
                  {step === 'idle' && (
                    <p className="text-xs text-rl-neutral-400 mt-1">PDF files only</p>
                  )}
                </div>
                {step === 'selected' && (
                  <StatusBadge status="READY" size="sm" />
                )}
              </div>
              <input
                id="file-input"
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
              />

              {/* Metadata fields */}
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <label className="rl-label block mb-1">Document type</label>
                  <select className="rl-select">
                    <option>Internal Study</option>
                    <option>Scientific Paper</option>
                    <option>Prior Response</option>
                    <option>Regulatory Letter</option>
                  </select>
                </div>
                <div>
                  <label className="rl-label block mb-1">Jurisdiction</label>
                  <select className="rl-select">
                    <option>India</option>
                    <option>EU</option>
                    <option>USA</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2 mt-5">
                <Button variant="ghost" size="sm" onClick={onClose} className="flex-1">Cancel</Button>
                <Button
                  variant="primary"
                  size="sm"
                  className="flex-1"
                  disabled={step !== 'selected'}
                  onClick={runUpload}
                >
                  Upload &amp; process
                </Button>
              </div>
            </>
          )}

          {step === 'uploading' && (
            <div className="py-6 flex flex-col items-center gap-3">
              <Loader2 size={28} className="text-rl-green-600 animate-spin" />
              <p className="text-sm font-medium text-rl-neutral-700">Uploading {fileName}…</p>
              <div className="w-full h-1.5 bg-rl-neutral-100 rounded-full overflow-hidden">
                <div className="h-full bg-rl-green-500 rounded-full animate-pulse w-1/2" />
              </div>
            </div>
          )}

          {step === 'processing' && (
            <div className="py-4 space-y-3">
              <p className="text-xs text-rl-neutral-500 mb-4 text-center">Processing document — this may take a moment</p>
              {PROCESSING_STAGES.map((stage, i) => (
                <div key={stage} className="flex items-center gap-3">
                  {i < processingStage ? (
                    <CheckCircle2 size={15} className="text-rl-green-600 shrink-0" />
                  ) : i === processingStage ? (
                    <Loader2 size={15} className="text-rl-green-500 animate-spin shrink-0" />
                  ) : (
                    <div className="w-[15px] h-[15px] rounded-full border-2 border-rl-neutral-200 shrink-0" />
                  )}
                  <span className={`text-xs ${i <= processingStage ? 'text-rl-neutral-800 font-medium' : 'text-rl-neutral-400'}`}>
                    {stage}
                  </span>
                </div>
              ))}
            </div>
          )}

          {step === 'complete' && (
            <div className="py-6 flex flex-col items-center gap-3 text-center">
              <div className="w-12 h-12 rounded-full bg-rl-green-50 border border-rl-green-200 flex items-center justify-center">
                <CheckCircle2 size={22} className="text-rl-green-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-rl-neutral-900">Document processed</p>
                <p className="text-xs text-rl-neutral-500 mt-1">{fileName} is ready to use as evidence</p>
              </div>
              <Button variant="primary" size="sm" onClick={onClose}>Done</Button>
            </div>
          )}

          {step === 'failed' && (
            <div className="py-6 flex flex-col items-center gap-3 text-center">
              <div className="w-12 h-12 rounded-full bg-rl-red-50 border border-rl-red-100 flex items-center justify-center">
                <AlertCircle size={22} className="text-rl-red-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-rl-neutral-900">Processing failed</p>
                <p className="text-xs text-rl-neutral-500 mt-1">Could not parse the document. Try again or contact support.</p>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
                <Button variant="secondary" size="sm" onClick={() => setStep('idle')}>Retry</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DocumentDetailDrawer({ doc, onClose }: { doc: Document; onClose: () => void }) {
  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40 animate-fade-in" onClick={onClose} />
      <aside className="fixed top-0 right-0 h-full w-[400px] bg-white z-50 flex flex-col shadow-2xl border-l border-rl-neutral-200 animate-slide-in-right">
        <div className="flex items-start justify-between px-5 py-4 border-b border-rl-neutral-200">
          <div>
            <h3 className="text-sm font-semibold text-rl-neutral-900 leading-snug">{doc.title}</h3>
            <div className="flex items-center gap-2 mt-1.5">
              <span className={`text-2xs font-medium px-2 py-0.5 rounded-full ${TYPE_COLORS[doc.type] ?? 'bg-rl-neutral-100 text-rl-neutral-600'}`}>
                {doc.type}
              </span>
              <span className="text-2xs text-rl-neutral-400">{doc.jurisdiction}</span>
              <StatusBadge status={doc.status} size="sm" />
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-rl-neutral-100 text-rl-neutral-500 transition-colors ml-3">
            <X size={16} />
          </button>
        </div>

        {/* Info */}
        <div className="px-5 py-4 border-b border-rl-neutral-100 bg-rl-neutral-50">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
            {[
              { label: 'Current Version', value: `v${doc.currentVersion}` },
              { label: 'Jurisdiction',    value: doc.jurisdiction },
              { label: 'Uploaded',        value: doc.uploadedAt },
              { label: 'Total Versions',  value: `${doc.versions.length}` },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className="rl-label mb-0.5">{label}</dt>
                <dd className="text-xs font-semibold text-rl-neutral-800">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Version history */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          <p className="rl-label mb-3">Version History</p>
          <div className="space-y-2">
            {doc.versions.map(v => (
              <div
                key={v.version}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-rl border ${
                  v.status === 'CURRENT'
                    ? 'border-rl-green-200 bg-rl-green-50'
                    : 'border-rl-neutral-200 bg-white'
                }`}
              >
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                  v.status === 'CURRENT' ? 'bg-rl-green-700 text-white' : 'bg-rl-neutral-100 text-rl-neutral-500'
                }`}>
                  v{v.version}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-medium ${v.status === 'CURRENT' ? 'text-rl-green-800' : 'text-rl-neutral-600'}`}>
                    {v.status === 'CURRENT' ? 'Current' : 'Superseded'}
                  </p>
                  <p className="text-2xs text-rl-neutral-400">{v.uploadedAt} · {v.chunkCount} chunks</p>
                </div>
                {v.status === 'SUPERSEDED' && (
                  <span className="text-2xs text-rl-neutral-400 italic">Archived</span>
                )}
              </div>
            ))}
          </div>
          <p className="text-2xs text-rl-neutral-400 mt-3 leading-relaxed">
            Superseded versions remain auditable — every citation permanently references the exact version it was based on.
          </p>
        </div>

        <div className="px-5 py-3 border-t border-rl-neutral-200 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1" icon={<FileUp size={12} />}>
            Upload new version
          </Button>
          <Button variant="ghost" size="sm">View document</Button>
        </div>
      </aside>
    </>
  );
}

export function DocumentsPage() {
  const [search, setSearch] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);

  const fetchDocs = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        const mapped = data.documents.map((d: any) => ({
          id: d.document_id,
          title: d.filename,
          type: d.doc_type,
          jurisdiction: d.jurisdiction || 'Unknown',
          currentVersion: d.current_version_number,
          status: 'READY',
          uploadedAt: new Date(d.created_at).toLocaleDateString(),
          versions: []
        }));
        setDocuments(mapped);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const filtered = documents.filter(d => {
    const matchesSearch = (d.title || '').toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-rl-neutral-900">Documents</h2>
          <p className="text-sm text-rl-neutral-500 mt-0.5">Regulatory evidence library</p>
        </div>
        <Button
          variant="primary"
          size="md"
          icon={<Upload size={14} />}
          onClick={() => setUploadOpen(true)}
        >
          Upload document
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-rl-neutral-400 pointer-events-none" />
          <input
            type="search"
            placeholder="Search documents…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="rl-input pl-8 text-xs"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter size={13} className="text-rl-neutral-400" />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="rl-select text-xs py-1.5 px-2 w-auto"
          >
            <option value="ALL">All statuses</option>
            <option value="READY">Ready</option>
            <option value="PROCESSING">Processing</option>
            <option value="APPROVED">Approved</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
        <p className="text-xs text-rl-neutral-400 ml-auto">{filtered.length} document{filtered.length !== 1 ? 's' : ''}</p>
      </div>

      {/* Table */}
      <div className="rl-card overflow-hidden">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-12 h-12 rounded-full bg-rl-neutral-100 flex items-center justify-center">
              <FolderOpen size={20} className="text-rl-neutral-400" />
            </div>
            <p className="text-sm text-rl-neutral-500 font-medium">No documents found</p>
            <p className="text-xs text-rl-neutral-400">Upload a PDF to begin building your evidence library</p>
            <Button variant="outline" size="sm" onClick={() => setUploadOpen(true)} icon={<Upload size={12} />}>
              Upload first document
            </Button>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-rl-neutral-200 bg-rl-neutral-50">
                {['Document', 'Type', 'Jurisdiction', 'Version', 'Status', 'Uploaded', ''].map(col => (
                  <th key={col} className="text-left px-4 py-2.5 rl-label font-medium">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(doc => (
                <tr
                  key={doc.id}
                  className="rl-table-row cursor-pointer"
                  onClick={() => setSelectedDoc(doc)}
                >
                  <td className="px-4 py-3">
                    <span className="font-medium text-rl-neutral-900 text-xs">{doc.title}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-2xs font-medium px-2 py-0.5 rounded-full ${TYPE_COLORS[doc.type] ?? ''}`}>
                      {doc.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-rl-neutral-500">{doc.jurisdiction}</td>
                  <td className="px-4 py-3 text-xs font-mono text-rl-neutral-700">v{doc.currentVersion}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-rl-neutral-500">{doc.uploadedAt}</td>
                  <td className="px-4 py-3">
                    <button
                      className="p-1 rounded hover:bg-rl-neutral-100 text-rl-neutral-400 transition-colors"
                      onClick={e => { e.stopPropagation(); setSelectedDoc(doc); }}
                    >
                      <MoreHorizontal size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals & Drawers */}
      {uploadOpen && <UploadModal onClose={() => setUploadOpen(false)} />}
      {selectedDoc && <DocumentDetailDrawer doc={selectedDoc} onClose={() => setSelectedDoc(null)} />}
    </div>
  );
}
