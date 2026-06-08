import clsx from "clsx";

export function Panel({ className, children }: { className?: string; children: React.ReactNode }) {
  return <section className={clsx("border-b border-black/10 bg-white/70", className)}>{children}</section>;
}

