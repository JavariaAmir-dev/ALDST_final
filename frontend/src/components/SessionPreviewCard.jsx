import { ArrowRight, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import ProgressBar from "./ProgressBar.jsx";

export default function SessionPreviewCard({ session }) {
  const progress = session.progress?.progress_percent || 0;
  const created = new Date(session.created_at).toLocaleDateString();

  return (
    <article className="rounded-2xl border border-[#ded8cb] bg-[#fffaf0] p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h3 className="truncate text-lg font-extrabold text-ink">{session.title}</h3>
          <p className="mt-1 text-sm font-semibold text-stone-600">{created}</p>
        </div>
        <span className={`w-fit rounded-full px-3 py-1 text-sm font-extrabold ${session.completed ? "bg-[#eef3ec] text-sageDark" : "bg-[#f8ecea] text-[#9b5c56]"}`}>
          {session.completed ? "Completed" : "In progress"}
        </span>
      </div>

      <div className="mt-4">
        <ProgressBar value={progress} label="Progress" />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link className="btn-soft !px-4 !py-2 text-sm" to={`/focus/${session.id}`}>
          Resume <ArrowRight size={16} />
        </Link>
        <Link className="btn-soft !px-4 !py-2 text-sm" to="/history">
          Open <ExternalLink size={16} />
        </Link>
      </div>
    </article>
  );
}
