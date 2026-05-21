import { ArrowLeft, ArrowRight, CheckCircle, Eye, Home, Minus, Moon, Plus, RotateCcw, Square, Sun, Volume2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../services/api.js";

function cardsFromSession(session) {
  if (session?.flashcards?.length) {
    return session.flashcards;
  }
  if (session?.quiz_questions?.length) {
    return session.quiz_questions.map((question, index) => ({
      question,
      answer: session.key_points?.[index] || session.summary || session.simplified_text,
      difficulty: "easy",
    }));
  }
  return [{
    question: "What is the main idea?",
    answer: session?.summary || session?.simplified_text || "Review this concept one step at a time.",
    difficulty: "easy",
  }];
}

export default function FocusMode() {
  const { id } = useParams();
  const [session, setSession] = useState(null);
  const [current, setCurrent] = useState(0);
  const [fontSize, setFontSize] = useState(18);
  const [flipped, setFlipped] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("aldst_focus_dark") === "true");
  const [reducedMotion, setReducedMotion] = useState(() => localStorage.getItem("aldst_reduced_motion") === "true");
  const [touchStart, setTouchStart] = useState(null);

  useEffect(() => {
    Promise.all([api.get(`/sessions/${id}`), api.get("/users/preferences")]).then(([sessionRes, prefRes]) => {
      setSession(sessionRes.data);
      setCurrent(sessionRes.data.progress?.current_chunk || 0);
      setFontSize(prefRes.data.font_size);
    });
  }, [id]);

  useEffect(() => {
    localStorage.setItem("aldst_focus_dark", String(darkMode));
  }, [darkMode]);

  useEffect(() => {
    localStorage.setItem("aldst_reduced_motion", String(reducedMotion));
  }, [reducedMotion]);

  const flashcards = useMemo(() => cardsFromSession(session), [session]);
  const total = flashcards.length || 1;
  const activeCard = flashcards[Math.min(current, total - 1)];
  const percent = Math.round(((current + 1) / total) * 100);

  const saveProgress = async (nextIndex, completed = false) => {
    const safeIndex = Math.min(Math.max(nextIndex, 0), total - 1);
    setCurrent(safeIndex);
    setFlipped(false);
    const { data } = await api.put(`/sessions/${id}/progress`, {
      current_chunk: safeIndex,
      total_chunks: total,
      completed,
    });
    setSession(data);
  };

  const showFeedback = (message) => {
    setFeedback(message);
    window.setTimeout(() => setFeedback(""), 1400);
  };

  const speakCard = () => {
    if (!("speechSynthesis" in window) || !activeCard) return;
    window.speechSynthesis.cancel();
    const text = flipped ? activeCard.answer : activeCard.question;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.86;
    utterance.pitch = 0.95;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeech = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  };

  const celebrateCompletion = () => {
    if (reducedMotion) return;
    setShowConfetti(true);
    window.setTimeout(() => setShowConfetti(false), 1800);
  };

  const next = () => {
    if (current >= total - 1) {
      saveProgress(total - 1, true);
      showFeedback("Session complete!");
      celebrateCompletion();
      return;
    }
    saveProgress(current + 1);
    showFeedback("Great job!");
  };

  const previous = () => saveProgress(current - 1);

  useEffect(() => {
    const handleKeyDown = (event) => {
    if (event.key === "ArrowRight") next();
    if (event.key === "ArrowLeft") previous();
      if (event.key.toLowerCase() === "a") speakCard();
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        setFlipped((value) => !value);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  const handleTouchEnd = (event) => {
    if (touchStart === null) return;
    const diff = touchStart - event.changedTouches[0].clientX;
    if (Math.abs(diff) > 45) {
      diff > 0 ? next() : previous();
    }
    setTouchStart(null);
  };

  if (!session) {
    return <div className="min-h-screen bg-stonewash p-6"><div className="card mx-auto max-w-2xl p-8 text-center">Loading focus space...</div></div>;
  }

  const shellClass = darkMode
    ? "bg-[#20231f] text-[#f4efe8]"
    : "bg-[#f6f1e8] text-ink";
  const panelClass = darkMode
    ? "border-[#5f6f5c] bg-[#2b3029] text-[#f4efe8]"
    : "border-[#ded8cb] bg-[#fffaf0]/90 text-ink";

  return (
    <div className={`min-h-screen px-4 py-6 transition-colors ${shellClass} ${reducedMotion ? "motion-reduced" : ""}`}>
      <div className="mx-auto max-w-5xl space-y-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-extrabold uppercase text-sageDark">Calm Focus Space</p>
            <h1 className="mt-2 text-3xl font-extrabold leading-tight">{session.title}</h1>
            <p className={`reading-area mt-2 max-w-2xl ${darkMode ? "text-stone-200" : "text-stone-700"}`}>
              One concept at a time. Flip when you are ready.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/" className="btn-soft" aria-label="Back to dashboard">
              <Home size={18} />
            </Link>
            <button className="btn-soft" onClick={() => setFontSize((value) => Math.max(18, value - 1))} aria-label="Decrease text size">
              <Minus size={18} />
            </button>
            <button className="btn-soft" onClick={() => setFontSize((value) => Math.min(32, value + 1))} aria-label="Increase text size">
              <Plus size={18} />
            </button>
            <button className="btn-soft" onClick={speakCard} aria-label="Read card aloud">
              <Volume2 size={18} />
            </button>
            <button className="btn-soft" onClick={stopSpeech} aria-label="Stop audio">
              <Square size={18} />
            </button>
            <button className="btn-soft" onClick={() => setDarkMode((value) => !value)} aria-pressed={darkMode} aria-label={darkMode ? "Use light mode" : "Use dark mode"}>
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button className="btn-soft" onClick={() => setReducedMotion((value) => !value)} aria-pressed={reducedMotion} aria-label="Toggle reduced motion">
              <Eye size={18} />
            </button>
          </div>
        </div>

        <div className="space-y-2" aria-label="Progress">
          <div className={`h-4 overflow-hidden rounded-full ${darkMode ? "bg-[#3a4038]" : "bg-[#ece3d4]"}`}>
            <div className="h-full rounded-full bg-gradient-to-r from-sageDark to-tide transition-all duration-700" style={{ width: `${percent}%` }} />
          </div>
          <div className="flex items-center justify-between text-sm font-extrabold">
            <span>Card {current + 1} of {total}</span>
            <span>{percent}% complete</span>
          </div>
        </div>

        <div className="relative min-h-[28rem]" aria-live="polite">
          {showConfetti && (
            <div className="confetti-layer" aria-hidden="true">
              {Array.from({ length: 22 }).map((_, index) => (
                <span key={index} className={`confetti-piece confetti-${(index % 6) + 1}`} style={{ left: `${6 + index * 4}%`, animationDelay: `${(index % 5) * 90}ms` }} />
              ))}
            </div>
          )}
          {feedback && (
            <div className={`completion-pop absolute left-1/2 top-0 z-10 -translate-x-1/2 rounded-2xl bg-[#f8ecea] px-5 py-3 font-extrabold text-[#9b5c56] shadow ${reducedMotion ? "motion-reduced" : ""}`}>
              {feedback}
            </div>
          )}

          <button
            key={current}
            type="button"
            className={`flashcard flashcard-fade mx-auto block w-full max-w-3xl text-left ${flipped ? "is-flipped" : ""} ${reducedMotion ? "motion-reduced" : ""}`}
            onClick={() => setFlipped((value) => !value)}
            onTouchStart={(event) => setTouchStart(event.touches[0].clientX)}
            onTouchEnd={handleTouchEnd}
            aria-label={flipped ? "Flashcard answer. Press to show question." : "Flashcard question. Press to show answer."}
          >
            <span className={`flashcard-inner rounded-[2rem] border shadow-lg ${panelClass}`}>
              <span className="flashcard-face flex flex-col justify-center">
                <span className="text-sm font-extrabold uppercase text-sageDark">Concept</span>
                <span className="mt-6 block leading-[1.75]" style={{ fontSize: `${fontSize + 7}px` }}>
                  {activeCard.question}
                </span>
                <span className="mt-8 inline-flex w-fit items-center gap-2 rounded-2xl bg-[#eef3ec] px-4 py-2 text-sm font-extrabold text-sageDark">
                  <RotateCcw size={16} /> Tap or press Space to reveal
                </span>
              </span>
              <span className="flashcard-face flashcard-back flex flex-col justify-center">
                <span className="text-sm font-extrabold uppercase text-sageDark">Takeaway</span>
                <span className="mt-6 block leading-[1.75]" style={{ fontSize: `${fontSize + 4}px` }}>
                  {activeCard.answer}
                </span>
                <span className="mt-8 inline-flex w-fit rounded-2xl bg-[#f8ecea] px-4 py-2 text-sm font-extrabold text-[#9b5c56]">
                  Concept mastered
                </span>
              </span>
            </span>
          </button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <button className="btn-soft" disabled={current === 0} onClick={previous}>
            <ArrowLeft size={18} /> Previous
          </button>
          <button className="btn-primary" onClick={next}>
            {current >= total - 1 ? <CheckCircle size={18} /> : null}
            {current >= total - 1 ? "Nice Work" : "I Understand This"}
            {current < total - 1 ? <ArrowRight size={18} /> : null}
          </button>
        </div>
      </div>
    </div>
  );
}
