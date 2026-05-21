export default function QuizCard({ question, index }) {
  return (
    <article className="rounded-2xl border border-[#ded8cb] bg-[#fbfaf7] p-4">
      <p className="text-sm font-extrabold uppercase text-sageDark">Question {index + 1}</p>
      <p className="mt-2 font-extrabold leading-8 text-ink">{question}</p>
    </article>
  );
}
