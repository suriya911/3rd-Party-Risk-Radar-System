import clsx from "clsx";

const SEV_COLOR: Record<number, string> = {
  1: "bg-slate-500/20 text-slate-400",
  2: "bg-blue-500/20 text-blue-400",
  3: "bg-yellow-500/20 text-yellow-400",
  4: "bg-orange-500/20 text-orange-400",
  5: "bg-red-500/20 text-red-400",
};

const SEV_LABEL: Record<number, string> = {
  1: "Low",
  2: "Minor",
  3: "Moderate",
  4: "High",
  5: "Critical",
};

export default function SeverityBadge({ severity }: { severity: number }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold",
        SEV_COLOR[severity] ?? SEV_COLOR[1]
      )}
    >
      {SEV_LABEL[severity] ?? severity} ({severity}/5)
    </span>
  );
}
