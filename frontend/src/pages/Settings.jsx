import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import LoadingButton from "../components/LoadingButton.jsx";
import api from "../services/api.js";

export default function Settings() {
  const [form, setForm] = useState({ preferred_language: "English", font_size: 18, reading_style: "simple" });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get("/users/preferences").then(({ data }) => setForm(data));
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setSaved(false);
    try {
      const { data } = await api.put("/users/preferences", form);
      setForm(data);
      setSaved(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <section className="card p-6">
        <p className="text-sm font-extrabold uppercase text-sageDark">Comfort Settings</p>
        <h1 className="mt-2 text-3xl font-extrabold leading-tight text-ink">Tune the learning space</h1>
        <form onSubmit={submit} className="mt-6 space-y-5">
          <label className="block">
            <span className="mb-2 block font-bold text-stone-700">Preferred language</span>
            <select className="field" value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}>
              <option>English</option>
              <option>Urdu</option>
              <option>Spanish</option>
              <option>French</option>
              <option>Arabic</option>
              <option>German</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block font-bold text-stone-700">Reading text size</span>
            <input className="field" type="number" min="18" max="32" value={form.font_size} onChange={(e) => setForm({ ...form, font_size: Number(e.target.value) })} />
          </label>
          <label className="block">
            <span className="mb-2 block font-bold text-stone-700">Reading flow</span>
            <select className="field" value={form.reading_style} onChange={(e) => setForm({ ...form, reading_style: e.target.value })}>
              <option value="simple">Simple</option>
              <option value="bullet">Bullet</option>
              <option value="step-by-step">Step-by-step</option>
            </select>
          </label>
          {saved && <p className="rounded-2xl bg-[#eef3ec] px-4 py-3 font-bold text-sageDark">Comfort settings saved</p>}
          <LoadingButton loading={loading}>
            <Save size={18} /> Save Settings
          </LoadingButton>
        </form>
      </section>
    </div>
  );
}
