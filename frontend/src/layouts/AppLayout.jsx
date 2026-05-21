import { Outlet, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";

export default function AppLayout() {
  const location = useLocation();
  const inFocusMode = location.pathname.startsWith("/focus/");

  return (
    <div className="min-h-screen bg-stonewash text-softCharcoal">
      {!inFocusMode && <Navbar />}
      <main className={`${inFocusMode ? "w-full" : "mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8"}`}>
        <Outlet />
      </main>
    </div>
  );
}
