import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { LOGO_ALT, LOGO_SRC, SITE_NAME, SITE_NAME_CONNECT, SITE_NAME_MARK } from "../lib/branding";

interface SiteBrandProps {
  to?: string;
  showName?: boolean;
  size?: "sm" | "sidebar" | "md" | "lg";
  variant?: "default" | "light";
  className?: string;
  onNavigate?: () => void;
}

const sizeClasses = {
  sm: { img: "size-8", text: "text-sm", width: 32, height: 32 },
  sidebar: { img: "size-12", text: "text-lg", width: 48, height: 48 },
  md: { img: "size-9", text: "text-base", width: 36, height: 36 },
  lg: { img: "size-11", text: "text-lg", width: 44, height: 44 },
};

function SiteName({ textClass, variant }: { textClass: string; variant: "default" | "light" }) {
  const isLight = variant === "light";

  return (
    <span className={cn("site-brand-name font-semibold tracking-tight", textClass)}>
      <span className={isLight ? "site-brand-mark--light" : "site-brand-mark"}>
        {SITE_NAME_MARK}
      </span>
      <span className={isLight ? "site-brand-connect--light" : "site-brand-connect"}>
        {SITE_NAME_CONNECT}
      </span>
    </span>
  );
}

export function SiteBrand({
  to,
  showName = true,
  size = "md",
  variant = "default",
  className,
  onNavigate,
}: SiteBrandProps) {
  const { img, text, width, height } = sizeClasses[size];

  const content = (
    <>
      <img
        src={LOGO_SRC}
        alt={LOGO_ALT}
        width={width}
        height={height}
        className={cn(img, "shrink-0 rounded-lg object-contain")}
        decoding="async"
      />
      {showName && <SiteName textClass={text} variant={variant} />}
    </>
  );

  const classes = cn("inline-flex min-w-0 items-center gap-2.5", className);

  if (to) {
    return (
      <Link to={to} onClick={onNavigate} className={classes} aria-label={`${SITE_NAME} — accueil`}>
        {content}
      </Link>
    );
  }

  return <div className={classes}>{content}</div>;
}
