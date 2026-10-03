interface CitationChipProps {
  code: string;
  onClick?: (code: string) => void;
  selected?: boolean;
  invalid?: boolean;
}

export function CitationChip({ code, onClick, selected = false, invalid = false }: CitationChipProps) {
  return (
    <button
      type="button"
      onClick={() => onClick?.(code)}
      title={`View evidence: ${code}`}
      className={`
        inline-flex items-center mx-0.5 px-1.5 py-0.5
        rounded font-mono text-2xs font-medium
        border transition-all duration-150 cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-rl-green-500 focus:ring-offset-1
        ${invalid
          ? 'bg-rl-red-50 text-rl-red-600 border-rl-red-200 hover:bg-rl-red-100'
          : selected
            ? 'bg-rl-green-700 text-white border-rl-green-700 shadow-sm'
            : 'bg-rl-green-50 text-rl-green-700 border-rl-green-200 hover:bg-rl-green-100 hover:border-rl-green-300'
        }
      `}
    >
      {code}
    </button>
  );
}
