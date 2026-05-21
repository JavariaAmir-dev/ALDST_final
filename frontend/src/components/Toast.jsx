import { CheckCircle2, X } from "lucide-react";

export function ToastViewport({ toasts, onDismiss }) {
  return (
    <div className="fixed right-4 top-4 z-50 grid w-[min(24rem,calc(100vw-2rem))] gap-3" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className="rounded-2xl border border-[#ded8cb] bg-[#fffaf0] p-4 shadow-lg">
          <div className="flex items-start gap-3">
            <CheckCircle2 className={toast.type === "error" ? "text-[#9b5c56]" : "text-sageDark"} size={21} />
            <div className="min-w-0 flex-1">
              <p className="font-extrabold text-ink">{toast.title}</p>
              {toast.message && <p className="mt-1 text-sm font-semibold text-stone-600">{toast.message}</p>}
            </div>
            <button className="rounded-full p-1 hover:bg-[#f3eadc]" onClick={() => onDismiss(toast.id)} aria-label="Dismiss notification">
              <X size={17} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
