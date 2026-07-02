import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../lib/cn";

export type ButtonVariant = "primary" | "accent" | "secondary" | "outline" | "blue";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "rounded-full bg-brand text-white hover:bg-brand-dark hover:scale-[1.02] focus-visible:ring-brand disabled:bg-neutral-300 disabled:text-neutral-500 disabled:hover:scale-100 shadow-lg shadow-brand/20 hover:shadow-xl hover:shadow-brand/25",
  accent:
    "rounded-full bg-accent text-accent-foreground hover:bg-accent-light focus-visible:ring-accent disabled:bg-neutral-300 disabled:text-neutral-500",
  secondary:
    "rounded-full bg-neutral-100 text-neutral-800 hover:bg-neutral-200 focus-visible:ring-neutral-400 disabled:bg-neutral-100 disabled:text-neutral-400",
  outline:
    "rounded-full border-2 border-brand/30 bg-transparent text-brand hover:border-brand hover:bg-brand-muted focus-visible:ring-brand disabled:border-neutral-300 disabled:text-neutral-400",
  blue:
    "rounded-full bg-brand text-white hover:bg-brand-dark focus-visible:ring-brand disabled:bg-neutral-300 disabled:text-neutral-500 shadow-lg shadow-brand/20",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      loading = false,
      fullWidth = false,
      disabled,
      className,
      children,
      type = "button",
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={loading}
        className={cn(
          "inline-flex min-h-11 items-center justify-center gap-2 px-5 py-2.5 text-body font-semibold transition-all duration-200 active:scale-[0.98]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed",
          fullWidth && "w-full",
          variantStyles[variant],
          className
        )}
        {...props}
      >
        {loading && (
          <span
            className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden="true"
          />
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
