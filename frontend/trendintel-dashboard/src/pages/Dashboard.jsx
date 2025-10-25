import { KPICard } from "@/components/KPICard";
import { TrendChart } from "@/components/TrendChart";
import { InsightCard } from "@/components/InsightCard";
import { BarChart2, TrendingUp, AlertTriangle } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-surface p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">TrendIntel Dashboard</h1>
        <div className="flex gap-4">
          <button className="px-4 py-2 rounded-xl bg-primary text-white shadow-soft">Export</button>
          <button className="px-4 py-2 rounded-xl border border-gray-200">Settings</button>
        </div>
      </header>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-8">
        <KPICard title="Avg Rating" value="4.1" icon={<BarChart2 className="text-primary"/>}/>
        <KPICard title="Top Material" value="Cotton" icon={<TrendingUp className="text-positive"/>}/>
        <KPICard title="Sentiment +" value="92%" icon={<TrendingUp className="text-positive"/>}/>
        <KPICard title="Complaints" value="Low" icon={<AlertTriangle className="text-warning"/>}/>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <TrendChart title="Material Sentiment Analysis" />
        <TrendChart title="Price Band vs Rating" />
      </div>

      {/* Insights */}
      <div>
        <h2 className="text-xl font-semibold mb-4">AI Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <InsightCard text="Soft cotton pastels trending +22% MoM"/>
          <InsightCard text="Fit complaints ↓ 18% compared to last month"/>
          <InsightCard text="Polyester blend satisfaction dropped to 3.6★"/>
        </div>
      </div>
    </div>
  );
}
