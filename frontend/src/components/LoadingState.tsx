import { HTMLAttributes } from "react";
import { cn } from "../lib/cn";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "rect" | "circle";
  width?: string;
  height?: string;
}

export function Skeleton({
  variant = "rect",
  width,
  height,
  className,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-neutral-200",
        variant === "text" && "h-4 rounded",
        variant === "rect" && "rounded-lg",
        variant === "circle" && "rounded-full",
        className
      )}
      style={{ width, height }}
      aria-hidden="true"
      {...props}
    />
  );
}

export function OffreCardSkeleton() {
  return (
    <div
      className="rounded-lg border border-neutral-200 bg-surface-card p-4 shadow-card"
      aria-busy="true"
      aria-label="Chargement de l'offre"
    >
      <div className="mb-3 flex justify-between">
        <Skeleton variant="rect" className="h-5 w-24" />
        <Skeleton variant="rect" className="h-5 w-16" />
      </div>
      <Skeleton variant="text" className="mb-2 w-full" />
      <Skeleton variant="text" className="mb-1 w-4/5" />
      <Skeleton variant="text" className="mb-4 w-1/3" />
      <Skeleton variant="rect" className="h-4 w-2/5" />
    </div>
  );
}

export interface LoadingStateProps {
  label?: string;
  count?: number;
  variant?: "spinner" | "skeleton";
}

export function LoadingState({
  label = "Chargement en cours…",
  count = 3,
  variant = "skeleton",
}: LoadingStateProps) {
  if (variant === "spinner") {
    return (
      <div
        className="flex flex-col items-center justify-center gap-4 py-16"
        role="status"
        aria-live="polite"
      >
        <span
          className="size-10 animate-spin rounded-full border-4 border-primary border-t-transparent"
          aria-hidden="true"
        />
        <p className="text-body text-neutral-600">{label}</p>
      </div>
    );
  }

  return (
    <div role="status" aria-live="polite" aria-label={label}>
      <span className="sr-only">{label}</span>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: count }).map((_, i) => (
          <OffreCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
