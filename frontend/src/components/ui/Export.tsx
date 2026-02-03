'use client'

import * as React from 'react'
import { Download, FileText, Table, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'

type ExportFormat = 'csv' | 'json' | 'pdf'

interface ExportConfig<T> {
  data: T[]
  filename: string
  columns?: Array<{
    key: keyof T
    header: string
    format?: (value: unknown) => string
  }>
  title?: string
  includeTimestamp?: boolean
}

// CSV Export
function exportToCSV<T>(config: ExportConfig<T>): void {
  const { data, filename, columns, includeTimestamp = true } = config

  if (data.length === 0) return

  const headers = columns
    ? columns.map((c) => c.header)
    : Object.keys(data[0] as object)

  const rows = data.map((item) => {
    if (columns) {
      return columns.map((col) => {
        const value = item[col.key]
        const formatted = col.format ? col.format(value) : String(value ?? '')
        // Escape quotes and wrap in quotes if contains comma
        return `"${formatted.replace(/"/g, '""')}"`
      })
    }
    return Object.values(item as object).map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`)
  })

  const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')

  const timestamp = includeTimestamp ? `_${new Date().toISOString().split('T')[0]}` : ''
  downloadFile(csvContent, `${filename}${timestamp}.csv`, 'text/csv')
}

// JSON Export
function exportToJSON<T>(config: ExportConfig<T>): void {
  const { data, filename, includeTimestamp = true } = config

  const exportData = {
    exportedAt: new Date().toISOString(),
    totalRecords: data.length,
    data,
  }

  const jsonContent = JSON.stringify(exportData, null, 2)
  const timestamp = includeTimestamp ? `_${new Date().toISOString().split('T')[0]}` : ''
  downloadFile(jsonContent, `${filename}${timestamp}.json`, 'application/json')
}

// PDF Export (creates a printable HTML that opens in new window)
function exportToPDF<T>(config: ExportConfig<T>): void {
  const { data, columns, title = 'Report' } = config

  const headers = columns ? columns.map((c) => c.header) : Object.keys((data[0] as object) || {})

  const tableRows = data
    .map((item) => {
      const cells = columns
        ? columns.map((col) => {
            const value = item[col.key]
            return col.format ? col.format(value) : String(value ?? '')
          })
        : Object.values(item as object).map((v) => String(v ?? ''))
      return `<tr>${cells.map((c) => `<td style="border:1px solid #ddd;padding:8px;">${escapeHtml(c)}</td>`).join('')}</tr>`
    })
    .join('')

  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${title}</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #333; }
        .meta { color: #666; margin-bottom: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th { background-color: #f5f5f5; border: 1px solid #ddd; padding: 12px 8px; text-align: left; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background-color: #fafafa; }
        @media print {
          body { padding: 0; }
          button { display: none; }
        }
      </style>
    </head>
    <body>
      <h1>${escapeHtml(title)}</h1>
      <div class="meta">
        <p>Generated: ${new Date().toLocaleString()}</p>
        <p>Total Records: ${data.length}</p>
      </div>
      <button onclick="window.print()" style="padding:10px 20px;cursor:pointer;margin-bottom:20px;">
        Print / Save as PDF
      </button>
      <table>
        <thead>
          <tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    </body>
    </html>
  `

  const blob = new Blob([htmlContent], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function escapeHtml(str: string): string {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

interface ExportButtonProps<T> {
  config: ExportConfig<T>
  format?: ExportFormat
  className?: string
  children?: React.ReactNode
}

export function ExportButton<T>({
  config,
  format = 'csv',
  className,
  children,
}: ExportButtonProps<T>) {
  const [exporting, setExporting] = React.useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      // Small delay for UI feedback
      await new Promise((resolve) => setTimeout(resolve, 100))
      
      switch (format) {
        case 'csv':
          exportToCSV(config)
          break
        case 'json':
          exportToJSON(config)
          break
        case 'pdf':
          exportToPDF(config)
          break
      }
    } finally {
      setExporting(false)
    }
  }

  const icons = {
    csv: <Table className="h-4 w-4" />,
    json: <FileText className="h-4 w-4" />,
    pdf: <FileText className="h-4 w-4" />,
  }

  return (
    <button
      onClick={handleExport}
      disabled={exporting || config.data.length === 0}
      className={clsx(
        'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
        'bg-gray-100 hover:bg-gray-200 text-gray-700',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
    >
      {exporting ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        icons[format]
      )}
      {children || `Export ${format.toUpperCase()}`}
    </button>
  )
}

interface ExportDropdownProps<T> {
  config: ExportConfig<T>
  className?: string
}

export function ExportDropdown<T>({
  config,
  className,
}: ExportDropdownProps<T>) {
  const [open, setOpen] = React.useState(false)
  const [exporting, setExporting] = React.useState<ExportFormat | null>(null)
  const dropdownRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExport = async (format: ExportFormat) => {
    setExporting(format)
    try {
      await new Promise((resolve) => setTimeout(resolve, 100))
      switch (format) {
        case 'csv':
          exportToCSV(config)
          break
        case 'json':
          exportToJSON(config)
          break
        case 'pdf':
          exportToPDF(config)
          break
      }
    } finally {
      setExporting(null)
      setOpen(false)
    }
  }

  return (
    <div ref={dropdownRef} className={clsx('relative', className)}>
      <button
        onClick={() => setOpen(!open)}
        disabled={config.data.length === 0}
        className={clsx(
          'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
          'bg-primary-600 hover:bg-primary-700 text-white',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        <Download className="h-4 w-4" />
        Export Report
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 rounded-lg bg-white shadow-lg border border-gray-200 py-1 z-50">
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting !== null}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {exporting === 'csv' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Table className="h-4 w-4" />
            )}
            Export as CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={exporting !== null}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {exporting === 'json' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            Export as JSON
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting !== null}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {exporting === 'pdf' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            Export as PDF
          </button>
        </div>
      )}
    </div>
  )
}

// Utility exports for direct use
export { exportToCSV, exportToJSON, exportToPDF }
