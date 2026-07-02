import { cn } from "../../lib/cn";

interface TogglePillProps {
  label: string;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function TogglePill({ label, selected, onClick, disabled }: TogglePillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      className={cn(
        "min-h-10 rounded-full border px-3.5 py-2 text-sm font-medium transition-all duration-200",
        selected
          ? "border-brand bg-brand text-white shadow-sm shadow-brand/25"
          : "border-neutral-200 bg-white text-neutral-700 hover:border-brand/35 hover:bg-brand-muted",
        disabled && "cursor-not-allowed opacity-60"
      )}
    >
      {label}
    </button>
  );
}
