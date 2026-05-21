export default function OutputCard({ title, children }) {
  return (
    <section className="card p-5">
      <h3 className="text-lg font-extrabold text-ink">{title}</h3>
      <div className="reading-area mt-4 text-stone-700">{children}</div>
    </section>
  );
}
