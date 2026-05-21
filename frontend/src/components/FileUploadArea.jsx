import { FileText, Upload } from "lucide-react";

export default function FileUploadArea({ file, onChange, onRemove }) {
  return (
    <div className="space-y-3">
      <label className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-sage/50 bg-[#fbfaf7] p-5 text-center font-bold text-sageDark transition hover:bg-[#eef3ec]">
        <Upload size={24} />
        <span>{file ? file.name : "Choose a PDF file"}</span>
        <span className="text-sm font-semibold text-stone-600">Text-based PDFs up to 10 MB work best.</span>
        <input className="sr-only" type="file" accept="application/pdf" onChange={(event) => onChange(event.target.files?.[0] || null)} />
      </label>
      {file && (
        <button type="button" className="btn-soft w-full" onClick={onRemove}>
          <FileText size={18} /> Remove PDF and use pasted text
        </button>
      )}
    </div>
  );
}
