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
    "bg-brand text-white hover:bg-brand-dark focus-visible:ring-brand disabled:bg-neutral-300 disabled:text-neutral-500 shadow-sm shadow-brand/20",
  accent:
    "bg-accent text-accent-foreground hover:bg-accent-light focus-visible:ring-accent disabled:bg-neutral-300 disabled:text-neutral-500",
  secondary:
    "bg-neutral-100 text-neutral-800 hover:bg-neutral-200 focus-visible:ring-neutral-400 disabled:bg-neutral-100 disabled:text-neutral-400",
  outline:
    "border-2 border-brand/30 bg-transparent text-brand hover:bg-brand hover:text-white focus-visible:ring-brand disabled:border-neutral-300 disabled:text-neutral-400",
  blue:
    "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-600 disabled:bg-neutral-300 disabled:text-neutral-500 shadow-sm shadow-blue-600/25",
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
          "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-body font-medium transition-all duration-200 active:scale-[0.98]",
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
