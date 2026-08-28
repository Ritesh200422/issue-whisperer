/**
 * ConfidenceBar — Renders a horizontal progress bar for confidence scores 0.0–1.0.
 */

type ConfidenceBarProps = {
  value: number; // 0.0 to 1.0
};

export function ConfidenceBar({ value }: ConfidenceBarProps) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  const colour =
    pct >= 75 ? "bg-green-500" : pct >= 45 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="w-full max-w-[120px] bg-gray-800 rounded-full h-1.5">
        <div
          className={`${colour} h-1.5 rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono font-semibold text-gray-300">{pct}%</span>
    </div>
  );
}
