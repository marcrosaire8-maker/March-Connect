import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { pageBadge, pageTitle } from "../../lib/design";

interface PageHeaderProps {
  badge: string;
  title: string;
  subtitle?: ReactNode;
  className?: string;
  centered?: boolean;
}

export function PageHeader({
  badge,
  title,
  subtitle,
  className,
  centered = true,
}: PageHeaderProps) {
  return (
    <header className={cn(centered && "text-center", "mb-10 sm:mb-12", className)}>
      <p className={cn(pageBadge, centered && "mx-auto", "mb-4")}>{badge}</p>
      <h1 className={pageTitle}>{title}</h1>
      {subtitle && (
        <div
          className={cn(
            "mt-5 text-lg text-neutral-600",
            centered && "mx-auto max-w-2xl"
          )}
        >
          {subtitle}
        </div>
      )}
    </header>
  );
}
