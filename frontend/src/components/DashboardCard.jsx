export default function DashboardCard({ children, className = "" }) {
  return (
    <section className={`card p-5 sm:p-6 ${className}`}>
      {children}
    </section>
  );
}
