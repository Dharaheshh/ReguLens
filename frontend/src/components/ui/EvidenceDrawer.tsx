import { X, ExternalLink, FileText, BookOpen } from 'lucide-react';
import type { Evidence } from '../../types';
import { Button } from './Button';

interface EvidenceDrawerProps {
  evidence: Evidence | null;
  open: boolean;
  onClose: () => void;
}

export function EvidenceDrawer({ evidence, open, onClose }: EvidenceDrawerProps) {
  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40 animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className="fixed top-0 right-0 h-full w-[420px] bg-white z-50 flex flex-col shadow-2xl border-l border-rl-neutral-200 animate-slide-in-right"
        role="complementary"
        aria-label="Evidence detail"
      >
        {/* Header */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-rl-neutral-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-semibold text-rl-green-700 bg-rl-green-50 border border-rl-green-200 px-2 py-0.5 rounded">
                {evidence?.code ?? '—'}
              </span>
              <span className="text-2xs text-rl-neutral-400 uppercase tracking-wider font-medium">
                {evidence?.sourceType}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-rl-neutral-900 leading-snug">
              {evidence?.documentTitle}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-rl-neutral-100 text-rl-neutral-500 transition-colors ml-3 shrink-0"
            aria-label="Close evidence drawer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Metadata grid */}
        <div className="px-5 py-3 border-b border-rl-neutral-100 bg-rl-neutral-50">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
            {[
              { label: 'Version',     value: evidence ? `v${evidence.documentVersion}` : '—' },
              { label: 'Source Type', value: evidence?.sourceType ?? '—' },
              { label: 'Page',        value: evidence ? `p. ${evidence.page}` : '—' },
              { label: 'Section',     value: evidence ? `§ ${evidence.section}` : '—' },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className="text-2xs text-rl-neutral-400 uppercase tracking-wider font-medium mb-0.5">{label}</dt>
                <dd className="text-xs font-medium text-rl-neutral-700">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Evidence excerpt */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={13} className="text-rl-neutral-400" />
            <span className="rl-label">Evidence Excerpt</span>
          </div>

          <div className="relative pl-4 before:absolute before:left-0 before:top-0 before:bottom-0 before:w-[3px] before:bg-rl-green-300 before:rounded-full">
            <p className="text-sm leading-relaxed text-rl-neutral-700 italic">
              "{evidence?.excerpt}"
            </p>
          </div>

          <div className="mt-4 p-3 bg-rl-neutral-50 border border-rl-neutral-200 rounded-rl text-xs text-rl-neutral-500">
            <span className="font-medium text-rl-neutral-600">Source: </span>
            {evidence?.documentTitle} · Version {evidence?.documentVersion} · Page {evidence?.page}, §{evidence?.section}
          </div>
        </div>

        {/* Footer actions */}
        <div className="px-5 py-3 border-t border-rl-neutral-200 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<ExternalLink size={12} />}
            className="flex-1"
          >
            Open document
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<FileText size={12} />}
            className="flex-1"
          >
            View in library
          </Button>
        </div>
      </aside>
    </>
  );
}
