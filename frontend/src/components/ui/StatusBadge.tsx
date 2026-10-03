import {
  CheckCircle2, XCircle, AlertTriangle, AlertCircle,
  Clock, Loader2, MinusCircle, CircleDashed,
} from 'lucide-react';

// type AnyStatus = ClaimStatus | RequirementCoverage | DocumentStatus | ResponseStatus | 'PROCESSING' | 'READY' | 'FAILED';

interface Config {
  label: string;
  className: string;
  dotClass: string;
  Icon: React.ComponentType<{ size?: number; className?: string }>;
}

const STATUS_CONFIG: Record<string, Config> = {
  SUPPORTED:              { label: 'Supported',              className: 'bg-rl-green-50  text-rl-green-700 border-rl-green-200',  dotClass: 'bg-rl-green-500',  Icon: CheckCircle2   },
  PARTIALLY_SUPPORTED:    { label: 'Partially Supported',    className: 'bg-rl-green-50  text-rl-green-600 border-rl-green-200',  dotClass: 'bg-rl-green-400',  Icon: MinusCircle    },
  UNSUPPORTED:            { label: 'Unsupported',            className: 'bg-rl-red-50    text-rl-red-700   border-rl-red-100',    dotClass: 'bg-rl-red-500',    Icon: XCircle        },
  OVERCLAIM:              { label: 'Overclaim',              className: 'bg-rl-amber-50  text-rl-amber-700 border-rl-amber-200',  dotClass: 'bg-rl-amber-500',  Icon: AlertTriangle  },
  POTENTIAL_CONTRADICTION:{ label: 'Potential Contradiction',className: 'bg-rl-amber-50  text-rl-amber-700 border-rl-amber-200',  dotClass: 'bg-rl-amber-500',  Icon: AlertTriangle  },
  COVERED:                { label: 'Covered',                className: 'bg-rl-green-50  text-rl-green-700 border-rl-green-200',  dotClass: 'bg-rl-green-500',  Icon: CheckCircle2   },
  PARTIALLY_COVERED:      { label: 'Partial',                className: 'bg-rl-amber-50  text-rl-amber-700 border-rl-amber-200',  dotClass: 'bg-rl-amber-500',  Icon: MinusCircle    },
  NOT_COVERED:            { label: 'Not Covered',            className: 'bg-rl-red-50    text-rl-red-600   border-rl-red-100',    dotClass: 'bg-rl-red-500',    Icon: XCircle        },
  READY:                  { label: 'Ready',                  className: 'bg-rl-green-50  text-rl-green-700 border-rl-green-200',  dotClass: 'bg-rl-green-500',  Icon: CheckCircle2   },
  APPROVED:               { label: 'Approved',               className: 'bg-rl-green-50  text-rl-green-700 border-rl-green-200',  dotClass: 'bg-rl-green-500',  Icon: CheckCircle2   },
  REJECTED:               { label: 'Rejected',               className: 'bg-rl-red-50    text-rl-red-700   border-rl-red-100',    dotClass: 'bg-rl-red-500',    Icon: XCircle        },
  FAILED:                 { label: 'Failed',                 className: 'bg-rl-red-50    text-rl-red-700   border-rl-red-100',    dotClass: 'bg-rl-red-500',    Icon: XCircle        },
  PROCESSING:             { label: 'Processing',             className: 'bg-blue-50      text-blue-700     border-blue-200',      dotClass: 'bg-blue-400',      Icon: Loader2        },
  PENDING_REVIEW:         { label: 'Pending Review',         className: 'bg-rl-amber-50  text-rl-amber-700 border-rl-amber-200',  dotClass: 'bg-rl-amber-500',  Icon: Clock          },
  DRAFT:                  { label: 'Draft',                  className: 'bg-rl-neutral-100 text-rl-neutral-600 border-rl-neutral-200', dotClass: 'bg-rl-neutral-400', Icon: CircleDashed },
  PENDING:                { label: 'Pending',                className: 'bg-rl-amber-50  text-rl-amber-700 border-rl-amber-200',  dotClass: 'bg-rl-amber-400',  Icon: Clock          },
  COMPLETE:               { label: 'Complete',               className: 'bg-rl-green-50  text-rl-green-700 border-rl-green-200',  dotClass: 'bg-rl-green-500',  Icon: CheckCircle2   },
};

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
}

export function StatusBadge({ status, size = 'sm', showIcon = true }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    className: 'bg-rl-neutral-100 text-rl-neutral-600 border-rl-neutral-200',
    dotClass: 'bg-rl-neutral-400',
    Icon: AlertCircle,
  };

  const { label, className, Icon } = config;
  const isSpinning = status === 'PROCESSING';

  const sizeClass = size === 'md'
    ? 'px-2.5 py-1 text-xs gap-1.5'
    : 'px-2 py-0.5 text-2xs gap-1';

  return (
    <span
      className={`
        inline-flex items-center rounded-full border font-medium
        ${sizeClass} ${className}
      `}
    >
      {showIcon && (
        <Icon
          size={size === 'md' ? 12 : 10}
          className={isSpinning ? 'animate-spin' : ''}
        />
      )}
      {label}
    </span>
  );
}
