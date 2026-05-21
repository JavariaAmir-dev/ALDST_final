import { ArrowRight, BookOpen, History, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DashboardCard from "../components/DashboardCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import SessionPreviewCard from "../components/SessionPreviewCard.jsx";
import StatCard from "../components/StatCard.jsx";
import api from "../services/api.js";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([api.get("/users/me"), api.get("/sessions", { params: { limit: 10 } }), api.get("/users/preferences")])
      .then(([userRes, sessionRes, prefRes]) => {
        setUser(userRes.data);
        setSessions(sessionRes.data);
        setPreferences(prefRes.data);
      })
      .catch(() => setError("Could not load your dashboard. Please refresh or try again."))
      .finally(() => setLoading(false));
  }, []);

  const lastSession = sessions[0];
  const completedCount = sessions.filter((item) => item.completed).length;
  const recentSessions = sessions.slice(0, 3);
  const readingStyle = preferences?.reading_style || "simple";

  return (
    <div className="space-y-6">
      {loading ? (
        <DashboardCard className="text-center">
          <LoadingSpinner label="Loading dashboard" />
        </DashboardCard>
      ) : error ? (
        <div className="rounded-2xl bg-[#f8ecea] p-5 font-bold text-[#9b5c56]">{error}</div>
      ) : (
        <>
          <DashboardCard>
            <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <p className="text-sm font-extrabold uppercase text-sageDark">Dashboard</p>
                <h1 className="mt-1 text-2xl font-extrabold leading-tight text-ink sm:text-3xl">
                  Welcome back{user ? `, ${user.username}` : ""}.
                </h1>
                <p className="mt-1 text-base font-semibold text-stone-700">Choose your next study step.</p>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Link to="/study" className="btn-primary">
                  <BookOpen size={18} /> Start New Study
                </Link>
                {lastSession ? (
                  <Link to={`/focus/${lastSession.id}`} className="btn-soft">
                    Continue Last Session <ArrowRight size={18} />
                  </Link>
                ) : (
                  <button className="btn-soft" type="button" disabled>
                    No session yet
                  </button>
                )}
              </div>
            </div>
          </DashboardCard>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard label="Total Sessions" value={sessions.length} />
            <StatCard label="Completed Sessions" value={completedCount} tone="rose" />
            <StatCard label="Reading Style" value={readingStyle} />
          </section>

          <section className="grid gap-6 lg:grid-cols-[1fr_18rem]">
            <DashboardCard>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-extrabold uppercase text-sageDark">Recent Activity</p>
                  <h2 className="mt-1 text-2xl font-extrabold text-ink">Recent Sessions</h2>
                </div>
                <Link className="btn-soft !px-4 !py-2 text-sm" to="/history">
                  View History <History size={16} />
                </Link>
              </div>

              <div className="mt-5 grid gap-3">
                {recentSessions.length ? (
                  recentSessions.map((session) => <SessionPreviewCard key={session.id} session={session} />)
                ) : (
                  <EmptyState
                    title="No study sessions yet"
                    message="Create your first study set from pasted text or a PDF."
                    action={<Link className="btn-primary" to="/study">Start New Study</Link>}
                  />
                )}
              </div>
            </DashboardCard>

            <DashboardCard>
              <Settings className="text-sageDark" size={23} />
              <h2 className="mt-4 text-xl font-extrabold text-ink">Accessibility</h2>
              <p className="mt-2 text-stone-700">
                Adjust font size and reading style in Settings.
              </p>
              <Link className="btn-soft mt-5 w-full" to="/settings">
                Open Settings
              </Link>
            </DashboardCard>
          </section>
        </>
      )}
    </div>
  );
}
