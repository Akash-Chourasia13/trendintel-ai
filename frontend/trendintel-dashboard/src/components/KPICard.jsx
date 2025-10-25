export function KPICard({ title, value, icon }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-soft flex items-center justify-between hover:shadow-md transition">
      <div>
        <h3 className="text-sm text-textSecondary font-medium">{title}</h3>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className="bg-surface p-3 rounded-lg">{icon}</div>
    </div>
  );
}
