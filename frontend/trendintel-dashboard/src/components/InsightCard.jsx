export function InsightCard({ text }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-soft border border-gray-100">
      <p className="text-base text-textPrimary leading-relaxed">{text}</p>
    </div>
  );
}
