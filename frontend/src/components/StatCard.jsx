export default function StatCard({ label, value, tone = "sage" }) {
  const toneClass = tone === "rose" ? "bg-[#f8ecea] text-[#9b5c56]" : "bg-[#eef3ec] text-sageDark";
  return (
    <div className="card p-5">
      <p className="text-sm font-bold text-stone-600">{label}</p>
      <p className={`mt-4 inline-flex min-w-16 rounded-2xl px-4 py-2 text-2xl font-extrabold ${toneClass}`}>{value}</p>
    </div>
  );
}
