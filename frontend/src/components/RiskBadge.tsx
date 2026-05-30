import clsx from "clsx";

interface Props {
  score: number | null;
  label: string | null;
  size?: "sm" | "lg";
}

const colorMap: Record<string, string> = {
  red:    "bg-red-500/20 text-red-400 border-red-500/40",
  orange: "bg-orange-500/20 text-orange-400 border-orange-500/40",
  yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
  green:  "bg-green-500/20 text-green-400 border-green-500/40",
};

const barColorMap: Record<string, string> = {
  red:    "bg-red-500",
  orange: "bg-orange-500",
  yellow: "bg-yellow-400",
  green:  "bg-green-500",
};

function getColor(score: number | null): string {
  if (score === null) return "green";
  if (score >= 75) return "red";
  if (score >= 50) return "orange";
  if (score >= 25) return "yellow";
  return "green";
}

export default function RiskBadge({ score, label, size = "sm" }: Props) {
  const color = getColor(score);
  const displayLabel = label ?? (score === null ? "Not scanned" : "Clear");

  return (
    <div className="flex items-center gap-2">
      <span
        className={clsx(
          "inline-flex items-center rounded border px-2 py-0.5 font-semibold uppercase tracking-wider",
          colorMap[color],
          size === "lg" ? "text-sm" : "text-xs"
        )}
      >
        {displayLabel}
      </span>
      {score !== null && (
        <div className="flex items-center gap-1.5">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
            <div
              className={clsx("h-full rounded-full transition-all", barColorMap[color])}
              style={{ width: `${score}%` }}
            />
          </div>
          <span className="text-xs text-slate-400">{score.toFixed(0)}</span>
        </div>
      )}
    </div>
  );
}
