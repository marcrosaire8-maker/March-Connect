import { HTMLAttributes } from "react";
import { cn } from "../lib/cn";

export type BadgeVariant = "secteur" | "premium" | "actif" | "inactif" | "neutral";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  secteur: "bg-primary/10 text-primary border border-primary/20",
  premium: "bg-accent/15 text-accent-dark border border-accent/30 font-semibold",
  actif: "bg-success-light text-success border border-success/20",
  inactif: "bg-neutral-100 text-neutral-600 border border-neutral-200",
  neutral: "bg-neutral-100 text-neutral-700 border border-neutral-200",
};

export function Badge({
  variant = "neutral",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-caption",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
