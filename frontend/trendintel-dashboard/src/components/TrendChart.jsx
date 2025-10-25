import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const data = [
  { name: "Cotton", sentiment: 4.1 },
  { name: "Silk", sentiment: 3.8 },
  { name: "Georgette", sentiment: 3.6 },
  { name: "Rayon", sentiment: 4.3 },
];

export function TrendChart({ title }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-soft">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="sentiment" fill="#3B82F6" radius={[6,6,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
