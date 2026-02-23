/**
 * Shared StatCard component used across all dashboard pages.
 *
 * Previously duplicated in 89 dashboard components.
 * Import this instead of defining inline.
 *
 * @example
 * import { StatCard } from '@/components/ui/StatCard'
 * <StatCard icon={<Shield />} title="Score" value="92%" subtitle="Compliance" />
 */

interface StatCardProps {
  icon: React.ReactNode
  title: string
  value: string
  subtitle: string
}

export function StatCard({ icon, title, value, subtitle }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}
