import { useState } from "react";
import { LogIn, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api.js";
import LoadingButton from "../components/LoadingButton.jsx";

function StudyMascot() {
  return (
    <div className="relative mx-auto h-72 w-72 sm:h-80 sm:w-80" aria-hidden="true">
      <div className="absolute left-1/2 top-2 h-64 w-56 -translate-x-1/2 rounded-[48%_48%_42%_42%] bg-[#7f9180] shadow-[0_24px_55px_rgba(47,48,44,0.18)]" />
      <div className="absolute left-[3.8rem] top-2 h-20 w-14 rotate-[-14deg] rounded-[80%_20%_70%_30%] bg-[#7f9180]" />
      <div className="absolute right-[3.8rem] top-2 h-20 w-14 rotate-[14deg] rounded-[20%_80%_30%_70%] bg-[#7f9180]" />
      <div className="absolute left-1/2 top-24 h-40 w-44 -translate-x-1/2 rounded-[48%] bg-[#fff7e8]" />
      <div className="absolute left-[5.7rem] top-[5.8rem] h-5 w-5 rounded-full bg-ink" />
      <div className="absolute right-[5.7rem] top-[5.8rem] h-5 w-5 rounded-full bg-ink" />
      <div className="absolute left-1/2 top-[6.6rem] h-4 w-7 -translate-x-1/2 rounded-full bg-[#4a5148]" />
      <div className="absolute left-[6.4rem] top-[8.1rem] h-1 w-8 rotate-[10deg] rounded-full bg-[#4a5148]" />
      <div className="absolute right-[6.4rem] top-[8.1rem] h-1 w-8 rotate-[-10deg] rounded-full bg-[#4a5148]" />
      <div className="absolute left-[5.4rem] top-[9.3rem] h-2 w-8 rotate-[-18deg] rounded-full bg-[#7f9180]" />
      <div className="absolute left-[7.3rem] top-[10.1rem] h-2 w-8 rotate-[-8deg] rounded-full bg-[#7f9180]" />
      <div className="absolute right-[5.4rem] top-[9.3rem] h-2 w-8 rotate-[18deg] rounded-full bg-[#7f9180]" />
      <div className="absolute right-[7.3rem] top-[10.1rem] h-2 w-8 rotate-[8deg] rounded-full bg-[#7f9180]" />
      <div className="absolute bottom-4 left-9 h-16 w-20 rotate-[-14deg] rounded-[50%] bg-[#6f816f]" />
      <div className="absolute bottom-4 right-9 h-16 w-20 rotate-[14deg] rounded-[50%] bg-[#6f816f]" />
      <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full bg-[#fffaf0] px-4 py-2 text-sm font-extrabold text-sageDark shadow-sm">
        ALDST
      </div>
    </div>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
      const payload = mode === "login" ? { email: form.email, password: form.password } : form;
      const { data } = await api.post(endpoint, payload);
      localStorage.setItem("aldst_token", data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-stonewash px-4 py-10">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-5xl items-center gap-8 lg:grid-cols-[1fr_0.9fr]">
        <section className="text-center lg:text-left">
          <div className="flex flex-col items-center gap-4 lg:items-start">
            <StudyMascot />
            <div className="inline-flex items-center gap-3 rounded-full bg-[#eef3ec] px-5 py-3 text-sageDark">
              <Sparkles size={24} />
              <span className="text-3xl font-extrabold leading-none text-ink sm:text-4xl">ALDST</span>
            </div>
          </div>
        </section>

        <section className="card p-6 sm:p-8">
          <div className="mb-6 flex rounded-2xl bg-[#f3eadc] p-1">
            {["login", "signup"].map((item) => (
              <button
                key={item}
                onClick={() => setMode(item)}
                className={`flex-1 rounded-2xl px-4 py-3 font-bold capitalize ${mode === item ? "bg-[#fffaf0] text-sageDark shadow-sm" : "text-stone-600"}`}
              >
                {item}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-4">
            {mode === "signup" && (
              <input className="field" placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            )}
            <input className="field" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            <input className="field" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6} />
            {error && <p className="rounded-2xl bg-[#f8ecea] px-4 py-3 text-sm font-bold text-[#9b5c56]">{error}</p>}
            <LoadingButton loading={loading} className="w-full">
              <LogIn size={18} />
              {mode === "login" ? "Login" : "Create Account"}
            </LoadingButton>
          </form>
        </section>
      </div>
    </main>
  );
}
