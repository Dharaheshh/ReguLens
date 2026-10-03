import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'destructive' | 'outline';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:     'bg-rl-green-700 text-white hover:bg-rl-green-800 focus:ring-rl-green-500 border-transparent shadow-rl-sm',
  secondary:   'bg-white text-rl-neutral-700 hover:bg-rl-neutral-50 focus:ring-rl-green-500 border-rl-neutral-200',
  ghost:       'bg-transparent text-rl-neutral-600 hover:bg-rl-neutral-100 focus:ring-rl-neutral-400 border-transparent',
  outline:     'bg-transparent text-rl-green-700 hover:bg-rl-green-50 focus:ring-rl-green-500 border-rl-green-300',
  destructive: 'bg-rl-red-600 text-white hover:bg-rl-red-700 focus:ring-rl-red-500 border-transparent shadow-rl-sm',
};

const SIZE_CLASSES: Record<Size, string> = {
  sm:  'px-2.5 py-1.5 text-xs gap-1.5',
  md:  'px-3.5 py-2   text-sm gap-2',
  lg:  'px-5   py-2.5 text-sm gap-2',
};

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  icon,
  iconRight,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center font-medium rounded-rl
        border transition-all duration-150 cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-offset-1
        disabled:opacity-50 disabled:cursor-not-allowed
        ${VARIANT_CLASSES[variant]}
        ${SIZE_CLASSES[size]}
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <Loader2 size={14} className="animate-spin shrink-0" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children}
      {iconRight && !loading && (
        <span className="shrink-0">{iconRight}</span>
      )}
    </button>
  );
}
