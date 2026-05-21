import { ArrowRight, Download } from "lucide-react";
import { Link } from "react-router-dom";
import ProgressBar from "./ProgressBar.jsx";

export default function SessionCard({ session, onExport }) {
  const preview = session.original_text.slice(0, 140);
  const progress = session.progress?.progress_percent || 0;
  return (
    <article className="card p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-lg font-bold text-ink">{session.title}</h3>
          <p className="mt-1 text-sm text-stone-600">{new Date(session.created_at).toLocaleString()}</p>
        </div>
        <span className={`w-fit rounded-lg px-3 py-1 text-sm font-semibold ${session.completed ? "bg-[#eef3ec] text-sageDark" : "bg-[#f8ecea] text-[#9b5c56]"}`}>
          {session.completed ? "Completed" : `${progress}% read`}
        </span>
      </div>
      <p className="mt-4 leading-7 text-stone-700">{preview}{session.original_text.length > 140 ? "..." : ""}</p>
      <div className="mt-4">
        <ProgressBar value={progress} label="Session completion" />
      </div>
      <div className="mt-5 flex flex-wrap gap-3">
        <Link className="btn-soft" to={`/focus/${session.id}`}>
          Resume Focus <ArrowRight size={18} />
        </Link>
        {onExport && (
          <>
            <button className="btn-soft" type="button" onClick={() => onExport(session, "pdf")}><Download size={18} /> PDF</button>
            <button className="btn-soft" type="button" onClick={() => onExport(session, "md")}>Markdown</button>
            <button className="btn-soft" type="button" onClick={() => onExport(session, "txt")}>TXT</button>
          </>
        )}
      </div>
    </article>
  );
}
