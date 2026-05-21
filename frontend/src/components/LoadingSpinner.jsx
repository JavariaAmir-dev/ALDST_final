export default function LoadingSpinner({ label = "Loading" }) {
  return (
    <span className="inline-flex items-center gap-2 font-bold text-sageDark" role="status" aria-live="polite">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-sage/30 border-t-sageDark" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
