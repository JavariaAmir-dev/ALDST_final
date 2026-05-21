export default function EmptyState({ icon: Icon, title, message, action }) {
  return (
    <section className="card p-8 text-center">
      {Icon && (
        <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#eef3ec] text-sageDark">
          <Icon size={26} />
        </span>
      )}
      <h2 className="mt-4 text-2xl font-extrabold text-ink">{title}</h2>
      <p className="reading-area mx-auto mt-3 max-w-xl text-stone-700">{message}</p>
      {action && <div className="mt-6">{action}</div>}
    </section>
  );
}
