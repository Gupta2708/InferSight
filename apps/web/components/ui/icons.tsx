import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function IconBase({ children, className, ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function ActivityIcon(props: IconProps) {
  return <IconBase {...props}><path d="M4 12h3l2-6 4 12 2-6h5" /></IconBase>;
}

export function MessageIcon(props: IconProps) {
  return <IconBase {...props}><path d="M5 6h14v10H8l-3 3V6Z" /></IconBase>;
}

export function DatabaseIcon(props: IconProps) {
  return <IconBase {...props}><ellipse cx="12" cy="5" rx="7" ry="3" /><path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5" /><path d="M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7" /></IconBase>;
}

export function CompareIcon(props: IconProps) {
  return <IconBase {...props}><path d="M7 7h10" /><path d="M7 17h10" /><path d="m14 4 3 3-3 3" /><path d="m10 14-3 3 3 3" /></IconBase>;
}

export function PlugIcon(props: IconProps) {
  return <IconBase {...props}><path d="M9 7V3" /><path d="M15 7V3" /><path d="M7 7h10v5a5 5 0 0 1-10 0V7Z" /><path d="M12 17v4" /></IconBase>;
}

export function TrashIcon(props: IconProps) {
  return <IconBase {...props}><path d="M4 7h16" /><path d="M10 11v6" /><path d="M14 11v6" /><path d="M6 7l1 14h10l1-14" /><path d="M9 7V4h6v3" /></IconBase>;
}

export function SendIcon(props: IconProps) {
  return <IconBase {...props}><path d="m4 12 16-8-6 16-3-7-7-1Z" /><path d="m11 13 4-4" /></IconBase>;
}

export function StopIcon(props: IconProps) {
  return <IconBase {...props}><rect x="6" y="6" width="12" height="12" rx="2" /></IconBase>;
}

export function PlayIcon(props: IconProps) {
  return <IconBase {...props}><path d="M8 5v14l11-7-11-7Z" /></IconBase>;
}

export function TraceIcon(props: IconProps) {
  return <IconBase {...props}><path d="M6 4v6" /><path d="M18 14v6" /><path d="M6 10c0 4 12 0 12 4" /><circle cx="6" cy="4" r="2" /><circle cx="18" cy="20" r="2" /></IconBase>;
}

export function CopyIcon(props: IconProps) {
  return <IconBase {...props}><rect x="8" y="8" width="11" height="11" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" /></IconBase>;
}

export function SparkIcon(props: IconProps) {
  return <IconBase {...props}><path d="M12 3v4" /><path d="M12 17v4" /><path d="M3 12h4" /><path d="M17 12h4" /><path d="m6 6 2.5 2.5" /><path d="m15.5 15.5 2.5 2.5" /><path d="m18 6-2.5 2.5" /><path d="m8.5 15.5-2.5 2.5" /></IconBase>;
}

export function SunIcon(props: IconProps) {
  return <IconBase {...props}><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" /></IconBase>;
}

export function MoonIcon(props: IconProps) {
  return <IconBase {...props}><path d="M20 14.6A8 8 0 0 1 9.4 4a7 7 0 1 0 10.6 10.6Z" /></IconBase>;
}
