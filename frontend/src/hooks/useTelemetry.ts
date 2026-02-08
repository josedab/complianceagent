import { api } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { TelemetrySnapshot, TelemetryEvent, MetricTimeSeries, AlertThreshold, HeatmapData } from '@/types/telemetry'

export function useTelemetrySnapshot() {
  return useQuery<TelemetrySnapshot>({
    queryKey: ['telemetry', 'snapshot'],
    queryFn: async () => {
      const { data } = await api.get('/telemetry/snapshot')
      return data
    },
    refetchInterval: 10000,
  })
}

export function useTelemetryEvents(limit = 20) {
  return useQuery<TelemetryEvent[]>({
    queryKey: ['telemetry', 'events', limit],
    queryFn: async () => {
      const { data } = await api.get('/telemetry/events', { params: { limit } })
      return data
    },
    refetchInterval: 5000,
  })
}

export function useTimeSeries(metricType: string, period = '24h', framework?: string) {
  return useQuery<MetricTimeSeries>({
    queryKey: ['telemetry', 'time-series', metricType, period, framework],
    queryFn: async () => {
      const { data } = await api.get(`/telemetry/time-series/${metricType}`, {
        params: { period, framework },
      })
      return data
    },
    refetchInterval: 30000,
  })
}

export function useAlertThresholds() {
  return useQuery<AlertThreshold[]>({
    queryKey: ['telemetry', 'thresholds'],
    queryFn: async () => {
      const { data } = await api.get('/telemetry/thresholds')
      return data
    },
  })
}

export function useHeatmapData(period = '7d') {
  return useQuery<HeatmapData>({
    queryKey: ['telemetry', 'heatmap', period],
    queryFn: async () => {
      const { data } = await api.get('/telemetry/heatmap', { params: { period } })
      return data
    },
    refetchInterval: 60000,
  })
}
