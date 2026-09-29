// Recharts wrappers. Colours follow the active Day/Night theme via useTheme()
// (Recharts takes JS colour props, not CSS classes). Each takes plain data
// arrays; tooltips format INR via the shared formatter.

import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  PieChart, Pie, Legend, LineChart, Line, CartesianGrid, AreaChart, Area,
} from 'recharts'
import { inr, CHART_COLORS } from '../lib/format'
import { useTheme } from '../theme/ThemeContext'

function moneyTip(v: any) { return inr(Number(v)) }

/** Shared axis/grid/tooltip styling derived from the current theme. */
function useChartTheme() {
  const { chart } = useTheme()
  const AXIS = { stroke: chart.axis, fontSize: 11 }
  const tooltipStyle = {
    contentStyle: { background: chart.tooltipBg, border: `1px solid ${chart.tooltipBorder}`, borderRadius: 12, fontSize: 12 },
    labelStyle: { color: chart.tooltipLabel },
    itemStyle: { color: chart.tooltipItem },
  }
  return { AXIS, GRID: chart.grid, tooltipStyle, legend: chart.legend, cursor: chart.cursor }
}

export function BarCard({
  data, xKey, yKey, height = 260, money = true, color = '#4f46e5', horizontal = false,
}: {
  data: any[]; xKey: string; yKey: string; height?: number; money?: boolean; color?: string; horizontal?: boolean
}) {
  const { AXIS, GRID, tooltipStyle, cursor } = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={{ top: 6, right: 12, bottom: 6, left: horizontal ? 8 : 0 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={!horizontal} horizontal={horizontal} />
        {horizontal ? (
          <>
            <XAxis type="number" {...AXIS} tickFormatter={money ? (v) => inr(v) : undefined} />
            <YAxis type="category" dataKey={xKey} {...AXIS} width={140} />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} {...AXIS} interval={0} angle={-12} textAnchor="end" height={50} />
            <YAxis {...AXIS} tickFormatter={money ? (v) => inr(v) : undefined} width={64} />
          </>
        )}
        <Tooltip {...tooltipStyle} formatter={money ? moneyTip : undefined} cursor={{ fill: cursor }} />
        <Bar dataKey={yKey} radius={[6, 6, 0, 0]} fill={color}>
          {data.map((_, i) => <Cell key={i} fill={color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function DonutCard({
  data, nameKey, valueKey, height = 260, money = true,
}: { data: any[]; nameKey: string; valueKey: string; height?: number; money?: boolean }) {
  const { tooltipStyle, legend } = useChartTheme()
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey={valueKey} nameKey={nameKey} innerRadius={58} outerRadius={92} paddingAngle={2} stroke="none">
          {data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
        </Pie>
        <Tooltip {...tooltipStyle} formatter={money ? moneyTip : undefined} />
        <Legend wrapperStyle={{ fontSize: 12, color: legend }} />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function LineCard({
  data, xKey, series, height = 260, money = true, area = false,
}: {
  data: any[]; xKey: string; series: { key: string; label: string; color?: string }[]
  height?: number; money?: boolean; area?: boolean
}) {
  const { AXIS, GRID, tooltipStyle, legend } = useChartTheme()
  const Chart: any = area ? AreaChart : LineChart
  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 6, right: 12, bottom: 6, left: 0 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} {...AXIS} />
        <YAxis {...AXIS} tickFormatter={money ? (v) => inr(v) : undefined} width={64} />
        <Tooltip {...tooltipStyle} formatter={money ? moneyTip : undefined} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: legend }} />}
        {series.map((s, i) => area
          ? <Area key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color ?? CHART_COLORS[i % CHART_COLORS.length]} fill={s.color ?? CHART_COLORS[i % CHART_COLORS.length]} fillOpacity={0.12} strokeWidth={2} />
          : <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color ?? CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={false} />
        )}
      </Chart>
    </ResponsiveContainer>
  )
}
