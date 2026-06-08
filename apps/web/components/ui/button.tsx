import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type ButtonVariant = "primary" | "secondary" | "ghost" | "warning" | "danger";

const variants: Record<ButtonVariant, string> = {
  primary: "border-signal/30 bg-signal text-[#07100f] hover:bg-signal/90",
  secondary: "border-black/10 bg-card text-ink hover:bg-paper",
  ghost: "border-transparent bg-transparent text-ink/70 shadow-none hover:bg-card hover:text-ink",
  warning: "border-amber-300/40 bg-amberline text-ink hover:bg-amberline/85",
  danger: "border-red-300/40 bg-red-600 text-white hover:bg-red-700"
};

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={clsx(
        "focus-ring inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
