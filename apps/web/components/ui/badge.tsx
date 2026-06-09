import clsx from "clsx";
import type { ReactNode } from "react";

const toneClasses = {
  success: "border-emerald-500/20 bg-emerald-500/[0.08] text-emerald-700 dark:text-emerald-300",
  warning: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300",
  error: "border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300",
  neutral: "border-black/10 bg-black/[0.035] text-ink/60 dark:border-white/10 dark:bg-white/[0.045]",
  info: "border-signal/20 bg-signal/10 text-signal"
};

export type BadgeTone = keyof typeof toneClasses;

const dotClasses: Record<BadgeTone, string> = {
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  neutral: "bg-ink/35",
  info: "bg-signal"
};

export function Badge({
  children,
  tone = "neutral",
  className
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4",
        toneClasses[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusChip({
  status,
  className
}: {
  status?: string | null;
  className?: string;
}) {
  const normalized = status || "unknown";
  const tone = statusTone(normalized);
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4",
        toneClasses[tone],
        className
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", dotClasses[tone])} />
      {normalized}
    </span>
  );
}

export function StatusDot({
  status,
  className
}: {
  status?: string | null;
  className?: string;
}) {
  const normalized = status || "unknown";
  const tone = statusTone(normalized);
  return (
    <span className={clsx("inline-flex items-center gap-1.5 text-[11px] font-medium leading-4", toneTextClasses[tone], className)}>
      <span className={clsx("h-1.5 w-1.5 rounded-full", dotClasses[tone])} />
      {normalized}
    </span>
  );
}

export function ProviderChip({ provider, className }: { provider?: string | null; className?: string }) {
  return <Badge tone="info" className={className}>{provider || "-"}</Badge>;
}

export function ModelChip({ model, className }: { model?: string | null; className?: string }) {
  return <Badge tone="neutral" className={className}>{model || "-"}</Badge>;
}

export function statusTone(status?: string | null): BadgeTone {
  if (status === "completed" || status === "enabled") return "success";
  if (status === "active") return "info";
  if (status === "configured" || status === "mock mode") return "info";
  if (status === "cancelled" || status === "streaming" || status === "pending" || status === "needs key") return "warning";
  if (status === "error" || status === "failed") return "error";
  return "neutral";
}

const toneTextClasses: Record<BadgeTone, string> = {
  success: "text-emerald-700 dark:text-emerald-300",
  warning: "text-amber-700 dark:text-amber-300",
  error: "text-red-700 dark:text-red-300",
  neutral: "text-ink/55",
  info: "text-signal"
};
