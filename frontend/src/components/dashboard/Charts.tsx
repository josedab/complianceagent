'use client'

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface ComplianceTrendData {
  date: string
  score: number
  compliant: number
  partial: number
  nonCompliant: number
}

interface RiskDistributionData {
  name: string
  value: number
  color: string
}

interface FrameworkComparisonData {
  framework: string
  current: number
  previous: number
}

const COLORS = {
  primary: '#3b82f6',
  success: '#22c55e',
  warning: '#eab308',
  danger: '#ef4444',
  gray: '#9ca3af',
}

export function ComplianceTrendChart({ data }: { data: ComplianceTrendData[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(value: number) => [`${value}%`, 'Compliance Score']}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke={COLORS.primary}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorScore)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ComplianceStackedChart({ data }: { data: ComplianceTrendData[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          <Legend />
          <Bar dataKey="compliant" stackId="a" fill={COLORS.success} name="Compliant" />
          <Bar dataKey="partial" stackId="a" fill={COLORS.warning} name="Partial" />
          <Bar dataKey="nonCompliant" stackId="a" fill={COLORS.danger} name="Non-Compliant" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RiskDistributionChart({ data }: { data: RiskDistributionData[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number, name: string) => [value, name]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function FrameworkComparisonChart({ data }: { data: FrameworkComparisonData[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 10, left: 60, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(value) => `${value}%`}
          />
          <YAxis
            type="category"
            dataKey="framework"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            width={50}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [`${value}%`]}
          />
          <Legend />
          <Bar dataKey="current" fill={COLORS.primary} name="Current" barSize={12} />
          <Bar dataKey="previous" fill={COLORS.gray} name="Previous Month" barSize={12} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ActivityTimelineChart({
  data,
}: {
  data: Array<{ date: string; count: number }>
}) {
  return (
    <div className="h-32 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            formatter={(value: number) => [value, 'Activities']}
          />
          <Line
            type="monotone"
            dataKey="count"
            stroke={COLORS.primary}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Sample data generators for demo purposes
export const generateTrendData = (): ComplianceTrendData[] => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
  return months.map((date, i) => ({
    date,
    score: 75 + Math.floor(Math.random() * 15) + i * 2,
    compliant: 35 + i * 2,
    partial: 8 - Math.floor(i / 2),
    nonCompliant: 5 - Math.floor(i / 3),
  }))
}

export const generateRiskData = (): RiskDistributionData[] => [
  { name: 'Low', value: 42, color: COLORS.success },
  { name: 'Medium', value: 28, color: COLORS.warning },
  { name: 'High', value: 18, color: '#f97316' },
  { name: 'Critical', value: 12, color: COLORS.danger },
]

export const generateFrameworkData = (): FrameworkComparisonData[] => [
  { framework: 'GDPR', current: 92, previous: 88 },
  { framework: 'HIPAA', current: 85, previous: 82 },
  { framework: 'SOC 2', current: 78, previous: 75 },
  { framework: 'PCI-DSS', current: 88, previous: 85 },
  { framework: 'ISO 27001', current: 72, previous: 68 },
]

export const generateActivityData = () => {
  return Array.from({ length: 14 }, (_, i) => ({
    date: `Day ${i + 1}`,
    count: Math.floor(Math.random() * 20) + 5,
  }))
}
