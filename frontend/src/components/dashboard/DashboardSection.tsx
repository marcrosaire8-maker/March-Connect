import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

interface DashboardSectionProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  sticky?: boolean;
  accent?: boolean;
}

export function DashboardSection({
  title,
  description,
  icon,
  action,
  children,
  className,
  sticky = false,
  accent = false,
}: DashboardSectionProps) {
  return (
    <section
      className={cn(
        "dashboard-section",
        accent && "dashboard-section-accent",
        sticky && "lg:sticky lg:top-0 lg:self-start",
        className
      )}
    >
      <header className="dashboard-section-header">
        <div className="flex min-w-0 items-start gap-3">
          {icon && (
            <span className="dashboard-section-icon" aria-hidden="true">
              {icon}
            </span>
          )}
          <div className="min-w-0">
            <h2 className="dashboard-section-title">{title}</h2>
            {description && (
              <p className="dashboard-section-desc">{description}</p>
            )}
          </div>
        </div>
        {action}
      </header>
      <div className="dashboard-section-body">{children}</div>
    </section>
  );
}
