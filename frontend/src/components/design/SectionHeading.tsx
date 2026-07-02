import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { sectionIconCircle } from "../../lib/design";

interface SectionHeadingProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  className?: string;
}

export function SectionHeading({
  icon: Icon,
  title,
  description,
  className,
}: SectionHeadingProps) {
  return (
    <div className={cn("mb-5 flex items-start gap-3", className)}>
      <div className={sectionIconCircle}>
        <Icon className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-800">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-neutral-600">{description}</p>
        )}
      </div>
    </div>
  );
}
