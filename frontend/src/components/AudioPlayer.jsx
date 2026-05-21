import { Download, Square, Volume2 } from "lucide-react";

export default function AudioPlayer({ script, title = "aldst-audio-script", onSpeak, onStop }) {
  const downloadScript = () => {
    const blob = new Blob([script || ""], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${title || "aldst-audio-script"}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <button className="btn-soft" onClick={onSpeak} type="button">
          <Volume2 size={18} /> Play in Browser
        </button>
        <button className="btn-soft" onClick={onStop} type="button">
          <Square size={18} /> Stop Audio
        </button>
        <button className="btn-soft" onClick={downloadScript} type="button">
          <Download size={18} /> Download Script
        </button>
      </div>
      <p className="whitespace-pre-wrap">{script}</p>
    </div>
  );
}
