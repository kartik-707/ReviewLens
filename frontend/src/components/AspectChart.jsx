/**
 * AspectChart.jsx
 * Recharts bar chart visualising per-aspect sentiment scores [-1, +1].
 * Bars are colour-coded by sentiment polarity (green/red/grey).
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const barColor = (sentiment) =>
  sentiment === "Positive" ? "#3d6b4f"
  : sentiment === "Negative" ? "#b03a2e"
  : "#7a7468";

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="custom-tooltip">
      <div className="tooltip-label">{d.fullName}</div>
      <div>Score: {d.score?.toFixed(3)}</div>
      <div>Mentions: {d.mention_count}</div>
      <div>+{d.positive_pct?.toFixed(0)}% / -{d.negative_pct?.toFixed(0)}%</div>
    </div>
  );
}

export default function AspectChart({ aspects }) {
  const data = aspects.slice(0, 10).map(a => ({
    name:          a.name.length > 10 ? a.name.slice(0, 9) + "…" : a.name,
    fullName:      a.name,
    score:         a.score,
    mention_count: a.mention_count,
    positive_pct:  a.positive_pct,
    negative_pct:  a.negative_pct,
    sentiment:     a.sentiment,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 4, right: 16, left: -16, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#d5d0c8" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontFamily: "DM Mono", fontSize: 10, fill: "#7a7468" }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          domain={[-1, 1]}
          tick={{ fontFamily: "DM Mono", fontSize: 10, fill: "#7a7468" }}
          axisLine={false} tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(13,13,15,0.04)" }} />
        <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={40}>
          {data.map((d, i) => <Cell key={i} fill={barColor(d.sentiment)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
