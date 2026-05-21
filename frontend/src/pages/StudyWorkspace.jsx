import { Headphones, Languages, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AudioPlayer from "../components/AudioPlayer.jsx";
import EmptyState from "../components/EmptyState.jsx";
import FileUploadArea from "../components/FileUploadArea.jsx";
import LoadingButton from "../components/LoadingButton.jsx";
import OutputCard from "../components/OutputCard.jsx";
import QuizCard from "../components/QuizCard.jsx";
import { ToastViewport } from "../components/Toast.jsx";
import useToast from "../hooks/useToast.js";
import api from "../services/api.js";

const TARGET_LANGUAGES = ["Urdu", "Arabic", "French", "Spanish", "German"];

export default function StudyWorkspace() {
  const [form, setForm] = useState({ title: "", original_text: "", reading_style: "simple" });
  const [session, setSession] = useState(null);
  const [translation, setTranslation] = useState(null);
  const [targetLanguage, setTargetLanguage] = useState("Urdu");
  const [translationLoading, setTranslationLoading] = useState(false);
  const [translationError, setTranslationError] = useState("");
  const [audio, setAudio] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);
  const [error, setError] = useState("");
  const { toasts, showToast, dismiss } = useToast();

  useEffect(() => {
    api.get("/users/preferences").then(({ data }) => {
      setForm((current) => ({ ...current, reading_style: data.reading_style }));
      if (TARGET_LANGUAGES.includes(data.preferred_language)) {
        setTargetLanguage(data.preferred_language);
      }
    });
  }, []);

  const generate = async (event) => {
    event.preventDefault();
    setLoading(true);
    setTranslation(null);
    setTranslationError("");
    setAudio(null);
    setError("");
    try {
      const { data } = pdfFile ? await uploadPdf() : await api.post("/sessions", form);
      setSession(data);
      showToast({ title: "Study set created", message: "Notes and flashcards are ready." });
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create the study set. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const uploadPdf = () => {
    const data = new FormData();
    data.append("title", form.title);
    data.append("reading_style", form.reading_style);
    data.append("file", pdfFile);
    return api.post("/sessions/from-pdf", data, { headers: { "Content-Type": "multipart/form-data" } });
  };

  const translate = async () => {
    if (!session) return;
    setTranslationLoading(true);
    setTranslation(null);
    setTranslationError("");
    try {
      const { data } = await api.post("/translations", { session_id: session.id, target_language: targetLanguage });
      setTranslation(data);
      showToast({ title: "Translation ready", message: `${targetLanguage} study material is available.` });
    } catch (err) {
      setTranslationError(err.response?.data?.detail || "Translation failed. Please try again.");
    } finally {
      setTranslationLoading(false);
    }
  };

  const makeAudio = async () => {
    const { data } = await api.post("/audio", { session_id: session.id, voice: "calm" });
    setAudio(data);
    speakScript(data.audio_script || session.summary);
    showToast({ title: "Audio script ready", message: "Browser speech playback has started." });
  };

  const speakScript = (script) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(script);
      utterance.rate = 0.86;
      utterance.pitch = 0.95;
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopAudio = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      showToast({ title: "Audio stopped", message: "Browser speech playback has ended." });
    }
  };

  return (
    <div className="grid gap-7 lg:grid-cols-[0.9fr_1.1fr]">
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
      <section className="card p-6">
        <p className="text-sm font-extrabold uppercase text-sageDark">Create a study set</p>
        <h1 className="mt-2 text-3xl font-extrabold leading-tight text-ink">Upload a PDF or paste text</h1>
        <form onSubmit={generate} className="mt-6 space-y-4">
          <input className="field" placeholder="Session title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <select className="field" value={form.reading_style} onChange={(e) => setForm({ ...form, reading_style: e.target.value })}>
            <option value="simple">Simple</option>
            <option value="bullet">Bullet</option>
            <option value="step-by-step">Step-by-step</option>
          </select>
          <FileUploadArea file={pdfFile} onChange={setPdfFile} onRemove={() => setPdfFile(null)} />
          <textarea
            className="field min-h-80 leading-[1.8]"
            placeholder={pdfFile ? "Optional: paste text here instead by removing the PDF." : "Paste your reading here..."}
            value={form.original_text}
            onChange={(e) => setForm({ ...form, original_text: e.target.value })}
            required={!pdfFile}
            minLength={pdfFile ? undefined : 20}
          />
          {error && <p className="rounded-2xl bg-[#f8ecea] p-4 font-bold text-[#9b5c56]">{error}</p>}
          <LoadingButton loading={loading} className="w-full">
            <Sparkles size={18} /> Build My Focus Set
          </LoadingButton>
        </form>
      </section>

      <section className="space-y-4">
        {!session && (
          <EmptyState
            title="Your study set will appear here"
            message="Upload a PDF or paste text to create simplified notes, flashcards, quiz questions, translation, and audio support."
          />
        )}
        {session && (
          <>
            <OutputCard title="Simplified Notes">
              <p className="whitespace-pre-wrap">{session.simplified_text}</p>
            </OutputCard>
            <OutputCard title="Short Summary">
              <p>{session.summary}</p>
            </OutputCard>
            <OutputCard title="Key Points">
              <ul className="list-inside list-disc space-y-2">
                {session.key_points.map((point) => <li key={point}>{point}</li>)}
              </ul>
            </OutputCard>
            <OutputCard title="Learning Flashcards">
              <div className="grid gap-3">
                {session.flashcards?.map((card, index) => (
                  <article key={`${card.question}-${index}`} className="rounded-2xl border border-[#ded8cb] bg-[#fbfaf7] p-4">
                    <p className="text-sm font-extrabold uppercase text-sageDark">Card {index + 1}</p>
                    <p className="mt-2 font-extrabold text-ink">{card.question}</p>
                    <p className="mt-2 leading-[1.8]">{card.answer}</p>
                  </article>
                ))}
              </div>
            </OutputCard>
            <OutputCard title="Quiz Questions">
              <div className="grid gap-3">
                {session.quiz_questions?.map((question, index) => <QuizCard key={`${question}-${index}`} question={question} index={index} />)}
              </div>
            </OutputCard>
            <div className="flex flex-wrap items-center gap-3">
              <Link className="btn-primary" to={`/focus/${session.id}`}>Start Focus Session</Link>
              <select className="field max-w-48" value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
                {TARGET_LANGUAGES.map((language) => <option key={language} value={language}>{language}</option>)}
              </select>
              <LoadingButton type="button" loading={translationLoading} onClick={translate}>
                <Languages size={18} /> Translate
              </LoadingButton>
              <button className="btn-soft" onClick={makeAudio}><Headphones size={18} /> Generate Audio</button>
            </div>
            {translationError && <p className="rounded-2xl bg-[#f8ecea] p-4 font-bold text-[#9b5c56]">{translationError}</p>}
            {translation && (
              <OutputCard title={`${translation.target_language} Translated Study Material`}>
                <p className="whitespace-pre-wrap leading-[1.8]">{translation.translated_text}</p>
              </OutputCard>
            )}
            {audio && (
              <OutputCard title="Audio-Assisted Study Script">
                <p className="font-semibold text-sageDark">{audio.audio_url}</p>
                <div className="mt-4">
                  <AudioPlayer script={audio.audio_script} title={session.title} onSpeak={() => speakScript(audio.audio_script)} onStop={stopAudio} />
                </div>
              </OutputCard>
            )}
          </>
        )}
      </section>
    </div>
  );
}
