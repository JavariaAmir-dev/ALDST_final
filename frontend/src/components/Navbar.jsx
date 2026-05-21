import { BookOpen, History, Home, LogOut, Settings, Sparkles } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/study", label: "Study", icon: BookOpen },
  { to: "/history", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Navbar() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("aldst_token");
    navigate("/login");
  };

  return (
    <header className="border-b border-[#ded8cb] bg-[#fffaf0]/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#eef3ec] text-sageDark" aria-hidden="true">
            <Sparkles size={21} />
          </span>
          <div>
            <p className="text-xl font-extrabold text-ink">ALDST</p>
            <p className="text-sm font-semibold text-stone-600">Learn Smarter. Stay Focused.</p>
          </div>
        </div>
        <nav className="flex flex-wrap items-center gap-2 overflow-x-auto pb-1" aria-label="Primary navigation">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-bold transition ${
                  isActive ? "bg-[#eef3ec] text-sageDark shadow-sm" : "text-stone-700 hover:bg-[#f3eadc]"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
          <button onClick={logout} className="btn-soft !px-4 !py-2 text-sm" title="Logout">
            <LogOut size={17} />
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
}
