/**
 * StatusBadge — Renders a coloured pill badge for verification/triage status values.
 * Used across the dashboard to surface agent decisions clearly.
 */

type StatusBadgeProps = {
  status: "confirmed" | "possibly_related" | "not_duplicate" | string;
  size?: "sm" | "md";
};

const STATUS_STYLES: Record<string, string> = {
  confirmed: "bg-green-950/60 text-green-400 border border-green-900",
  possibly_related: "bg-yellow-950/60 text-yellow-400 border border-yellow-900",
  not_duplicate: "bg-gray-800 text-gray-400 border border-gray-700",
  verified: "bg-green-950/60 text-green-400 border border-green-900",
  failed: "bg-red-950/60 text-red-400 border border-red-900",
};

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const sizeClass = size === "md" ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs";
  const style = STATUS_STYLES[status] ?? "bg-gray-800 text-gray-400 border border-gray-700";

  return (
    <span className={`inline-flex items-center rounded-full font-bold uppercase tracking-wide ${sizeClass} ${style}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
