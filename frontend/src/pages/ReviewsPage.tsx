import { CheckCircle2 } from 'lucide-react';

export function ReviewsPage() {
  return (
    <div className="flex flex-col h-full animate-fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-rl-ink">Reviews & Approval</h2>
        <p className="text-sm text-rl-neutral-500 mt-1">Human-in-the-loop verification queue.</p>
      </div>

      <div className="rl-card p-12 flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-rl-green-50 flex items-center justify-center mb-4">
          <CheckCircle2 size={24} className="text-rl-green-600" />
        </div>
        <h3 className="text-lg font-semibold text-rl-ink mb-1">Queue is empty</h3>
        <p className="text-sm text-rl-neutral-500 max-w-sm">
          There are currently no AI drafts waiting for human review. Run a new query in the Query Workspace to generate a draft.
        </p>
      </div>
    </div>
  );
}
