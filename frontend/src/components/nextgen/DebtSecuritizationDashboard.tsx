'use client'

import { useState } from 'react'
import { Banknote, BarChart3, Clock, Award } from 'lucide-react'

type Priority = 'critical' | 'high' | 'medium' | 'low'

interface DebtItem {
  id: string
  title: string
  description: string
  priority: Priority
  framework: string
  control: string
  riskScore: number
  costOfDelayPerDay: number
  accruedInterest: number
  remediationCost: number
  daysOutstanding: number
  assignedTeam: string
}

const priorityConfig: Record<Priority, { color: string; bg: string }> = {
  critical: { color: 'text-red-700', bg: 'bg-red-100' },
  high: { color: 'text-orange-700', bg: 'bg-orange-100' },
  medium: { color: 'text-yellow-700', bg: 'bg-yellow-100' },
  low: { color: 'text-blue-700', bg: 'bg-blue-100' },
}

const MOCK_DEBT: DebtItem[] = [
  { id: '1', title: 'Missing encryption for user PII at rest', description: 'User table stores email and phone in plaintext.',
    priority: 'critical', framework: 'GDPR', control: 'Art. 32', riskScore: 9.2, costOfDelayPerDay: 150, accruedInterest: 4500, remediationCost: 2000, daysOutstanding: 30, assignedTeam: 'Platform' },
  { id: '2', title: 'Incomplete audit logging on admin endpoints', description: '15 admin endpoints lack structured audit logging.',
    priority: 'high', framework: 'SOC 2', control: 'CC7.2', riskScore: 7.5, costOfDelayPerDay: 85, accruedInterest: 1700, remediationCost: 1200, daysOutstanding: 20, assignedTeam: 'Security' },
  { id: '3', title: 'Outdated dependency with known CVE', description: 'lodash@4.17.15 has CVE-2021-23337.',
    priority: 'high', framework: 'PCI-DSS', control: 'Req. 6.2', riskScore: 6.8, costOfDelayPerDay: 65, accruedInterest: 975, remediationCost: 400, daysOutstanding: 15, assignedTeam: 'Frontend' },
  { id: '4', title: 'Missing consent banner for analytics cookies', description: 'Analytics tracking runs before user consent on EU visitors.',
    priority: 'medium', framework: 'GDPR', control: 'Art. 7', riskScore: 5.5, costOfDelayPerDay: 40, accruedInterest: 400, remediationCost: 800, daysOutstanding: 10, assignedTeam: 'Frontend' },
  { id: '5', title: 'No data retention policy enforcement', description: 'User data retained indefinitely.',
    priority: 'medium', framework: 'GDPR', control: 'Art. 5(1)(e)', riskScore: 6.0, costOfDelayPerDay: 55, accruedInterest: 1650, remediationCost: 1500, daysOutstanding: 30, assignedTeam: 'Backend' },
  { id: '6', title: 'Password policy below NIST guidelines', description: 'Current: 8 chars min, no complexity.',
    priority: 'low', framework: 'SOC 2', control: 'CC6.1', riskScore: 4.0, costOfDelayPerDay: 25, accruedInterest: 250, remediationCost: 600, daysOutstanding: 10, assignedTeam: 'Security' },
]

const totalDebt = MOCK_DEBT.reduce((s, d) => s + d.remediationCost + d.accruedInterest, 0)
const dailyAccrual = MOCK_DEBT.reduce((s, d) => s + d.costOfDelayPerDay, 0)
const criticalCount = MOCK_DEBT.filter(d => d.priority === 'critical').length
const creditRating = criticalCount >= 2 ? 'BB' : criticalCount === 1 ? 'BBB' : 'A'

export default function DebtSecuritizationDashboard() {
  const [priorityFilter, setPriorityFilter] = useState<string>('all')

  const filtered = priorityFilter === 'all' ? MOCK_DEBT : MOCK_DEBT.filter(d => d.priority === priorityFilter)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Banknote className="h-7 w-7 text-amber-600" /> Compliance Debt</h1>
        <p className="text-gray-500 mt-1">Track compliance debt as financial instruments with risk scoring</p>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
          <div className="text-sm text-red-600">Total Debt</div>
          <div className="text-2xl font-bold text-red-700">${totalDebt.toLocaleString()}</div>
        </div>
        <div className="bg-orange-50 rounded-lg border border-orange-200 p-4">
          <div className="text-sm text-orange-600">Daily Accrual</div>
          <div className="text-2xl font-bold text-orange-700">${dailyAccrual}/day</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Debt Items</div>
          <div className="text-2xl font-bold">{MOCK_DEBT.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Critical</div>
          <div className="text-2xl font-bold text-red-600">{criticalCount}</div>
        </div>
        <div className={`rounded-lg border p-4 ${creditRating === 'A' ? 'bg-green-50 border-green-200' : creditRating === 'BBB' ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
          <div className="text-sm text-gray-500 flex items-center gap-1"><Award className="h-3 w-3" /> Credit Rating</div>
          <div className="text-2xl font-bold">{creditRating}</div>
        </div>
      </div>

      {/* Debt by Framework */}
      <div className="bg-white rounded-lg border p-5">
        <h3 className="font-semibold mb-3 flex items-center gap-2"><BarChart3 className="h-5 w-5 text-amber-600" /> Debt by Framework</h3>
        <div className="space-y-2">
          {Array.from(new Set(MOCK_DEBT.map(d => d.framework))).map(fw => {
            const fwDebt = MOCK_DEBT.filter(d => d.framework === fw).reduce((s, d) => s + d.remediationCost + d.accruedInterest, 0)
            const pct = (fwDebt / totalDebt) * 100
            return (
              <div key={fw}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{fw}</span>
                  <span className="font-medium">${fwDebt.toLocaleString()} ({pct.toFixed(0)}%)</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {['all', 'critical', 'high', 'medium', 'low'].map(p => (
          <button key={p} onClick={() => setPriorityFilter(p)}
            className={`px-3 py-1 rounded-full text-sm ${priorityFilter === p ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            {p.charAt(0).toUpperCase() + p.slice(1)}
          </button>
        ))}
      </div>

      {/* Debt Items */}
      <div className="space-y-3">
        {filtered.map(item => {
          const cfg = priorityConfig[item.priority]
          return (
            <div key={item.id} className="bg-white rounded-lg border p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${cfg.bg} ${cfg.color}`}>{item.priority}</span>
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{item.framework}</span>
                    <span className="text-xs text-gray-400">{item.control}</span>
                  </div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="text-sm text-gray-600">{item.description}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{item.daysOutstanding}d outstanding</span>
                    <span>Team: {item.assignedTeam}</span>
                    <span>Risk: {item.riskScore}/10</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Remediation</div>
                  <div className="font-bold">${item.remediationCost.toLocaleString()}</div>
                  <div className="text-xs text-red-500">+${item.accruedInterest.toLocaleString()} interest</div>
                  <div className="text-xs text-orange-500">${item.costOfDelayPerDay}/day</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
