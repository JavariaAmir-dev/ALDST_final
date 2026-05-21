import { useEffect, useState } from "react";
import StatCard from "../components/StatCard.jsx";
import api from "../services/api.js";

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    api.get("/analytics").then(({ data }) => setAnalytics(data));
  }, []);

  if (!analytics) {
    return <div className="card p-8 text-center">Loading learning progress...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-extrabold uppercase text-sageDark">Learning Progress</p>
        <h1 className="mt-2 text-3xl font-extrabold text-ink">Your steady wins</h1>
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Focus Sessions Started" value={analytics.total_sessions} />
        <StatCard label="Concept Sets Completed" value={analytics.completed_sessions} tone="rose" />
        <StatCard label="Learning Momentum" value={`${analytics.average_progress}%`} />
        <StatCard label="Favorite Reading Flow" value={analytics.most_used_reading_style} tone="rose" />
        <StatCard label="Translation Language" value={analytics.most_used_translation_language} />
      </section>
    </div>
  );
}
