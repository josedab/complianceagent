// Telemetry Types
export interface TelemetrySnapshot {
  overall_score: number
  violation_count: number
  requirement_coverage: number
  drift_score: number
  risk_score: number
  audit_readiness: number
  frameworks: Record<string, number>
  repositories: Record<string, number>
  timestamp: string | null
}

export interface TelemetryMetric {
  id: string
  metric_type: string
  value: number
  previous_value: number | null
  framework: string | null
  repository: string | null
  timestamp: string | null
}

export interface TelemetryEvent {
  id: string
  event_type: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  framework: string | null
  repository: string | null
  metric_value: number | null
  timestamp: string | null
}

export interface AlertThreshold {
  id: string
  metric_type: string
  operator: string
  value: number
  severity: string
  channels: string[]
  enabled: boolean
  cooldown_minutes: number
}

export interface MetricTimeSeries {
  metric_type: string
  period: string
  framework: string | null
  data_points: { value: number; timestamp: string | null }[]
  latest_value: number | null
  trend: number | null
}

export interface HeatmapData {
  period: string
  frameworks: Record<string, { date: string; score: number }[]>
}
