export default function ProgressBar({ value = 0, label = "Progress" }) {
  const safeValue = Math.min(100, Math.max(0, Number(value) || 0));
  return (
    <div className="space-y-2" aria-label={label}>
      <div className="flex items-center justify-between text-sm font-extrabold text-stone-700">
        <span>{label}</span>
        <span>{safeValue}%</span>
      </div>
      <div className="h-4 overflow-hidden rounded-full bg-[#ece3d4]">
        <div className="h-full rounded-full bg-gradient-to-r from-sageDark to-tide transition-all duration-700" style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  );
}
