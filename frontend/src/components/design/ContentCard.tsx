import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";
import { contentCard, contentCardAccent, contentCardElevated } from "../../lib/design";

type ContentCardVariant = "default" | "elevated" | "accent";

interface ContentCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: ContentCardVariant;
  padding?: "none" | "sm" | "md" | "lg";
}

const variantClass: Record<ContentCardVariant, string> = {
  default: contentCard,
  elevated: contentCardElevated,
  accent: contentCardAccent,
};

const paddingClass = {
  none: "",
  sm: "p-4",
  md: "p-5",
  lg: "p-6 sm:p-8",
};

export function ContentCard({
  children,
  variant = "default",
  padding = "lg",
  className,
  ...props
}: ContentCardProps) {
  return (
    <div
      className={cn(variantClass[variant], paddingClass[padding], className)}
      {...props}
    >
      {children}
    </div>
  );
}
