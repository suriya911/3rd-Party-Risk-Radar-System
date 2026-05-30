import clsx from "clsx";

const CAT_COLOR: Record<string, string> = {
  Security:      "bg-red-500/10 text-red-300 border border-red-500/30",
  Financial:     "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30",
  Operational:   "bg-blue-500/10 text-blue-300 border border-blue-500/30",
  Regulatory:    "bg-purple-500/10 text-purple-300 border border-purple-500/30",
  Reputational:  "bg-pink-500/10 text-pink-300 border border-pink-500/30",
};

export default function CategoryBadge({ category }: { category: string }) {
  return (
    <span className={clsx("inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium", CAT_COLOR[category])}>
      {category}
    </span>
  );
}
