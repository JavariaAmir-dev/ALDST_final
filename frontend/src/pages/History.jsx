import { BookOpen, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import SessionCard from "../components/SessionCard.jsx";
import { ToastViewport } from "../components/Toast.jsx";
import useToast from "../hooks/useToast.js";
import api from "../services/api.js";

export default function History() {
  const [sessions, setSessions] = useState([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { toasts, showToast, dismiss } = useToast();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError("");
      const params = { q: query || undefined, limit: 50 };
      if (status !== "all") {
        params.completed = status === "completed";
      }
      api.get("/sessions", { params })
        .then(({ data }) => setSessions(data))
        .catch(() => setError("Could not load your study history."))
        .finally(() => setLoading(false));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query, status]);

  const exportSession = async (session, format) => {
    const { data } = await api.get(`/sessions/${session.id}/export`, {
      params: { format },
      responseType: "blob",
    });
    const url = URL.createObjectURL(data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${session.title || "aldst-session"}.${format === "markdown" ? "md" : format}`;
    link.click();
    URL.revokeObjectURL(url);
    showToast({ title: "Export downloaded", message: `${session.title} was saved as ${format.toUpperCase()}.` });
  };

  return (
    <div className="space-y-6">
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
      <div>
        <p className="text-sm font-bold uppercase tracking-normal text-sageDark">History</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Previous Study Sessions</h1>
      </div>

      <section className="card grid gap-3 p-4 md:grid-cols-[1fr_13rem]">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-stone-500" size={19} />
          <input
            className="field pl-12"
            placeholder="Search by title or text..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <select className="field" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">All sessions</option>
          <option value="active">In progress</option>
          <option value="completed">Completed</option>
        </select>
      </section>

      {loading ? (
        <div className="card p-8 text-center"><LoadingSpinner label="Loading history" /></div>
      ) : error ? (
        <div className="rounded-2xl bg-[#f8ecea] p-5 font-bold text-[#9b5c56]">{error}</div>
      ) : sessions.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No sessions found"
          message={query ? "Try a different search term or clear the filter." : "Create a study set first, then your notes and progress will appear here."}
          action={<Link className="btn-primary" to="/study">Start New Study</Link>}
        />
      ) : (
        <div className="grid gap-4">
          {sessions.map((session) => <SessionCard key={session.id} session={session} onExport={exportSession} />)}
        </div>
      )}
    </div>
  );
}
