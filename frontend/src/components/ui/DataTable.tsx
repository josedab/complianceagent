'use client'

import * as React from 'react'
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'

type SortDirection = 'asc' | 'desc' | null

interface Column<T> {
  key: keyof T | string
  header: string
  sortable?: boolean
  render?: (item: T, index: number) => React.ReactNode
  className?: string
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  pageSize?: number
  searchable?: boolean
  searchPlaceholder?: string
  searchKeys?: (keyof T)[]
  onRowClick?: (item: T) => void
  emptyMessage?: string
  className?: string
  selectable?: boolean
  selectedIds?: Set<string>
  onSelectionChange?: (ids: Set<string>) => void
  getRowId?: (item: T) => string
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  pageSize = 10,
  searchable = false,
  searchPlaceholder = 'Search...',
  searchKeys = [],
  onRowClick,
  emptyMessage = 'No data available',
  className,
  selectable = false,
  selectedIds = new Set(),
  onSelectionChange,
  getRowId = (item) => String(item.id),
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = React.useState<string | null>(null)
  const [sortDirection, setSortDirection] = React.useState<SortDirection>(null)
  const [currentPage, setCurrentPage] = React.useState(1)
  const [searchQuery, setSearchQuery] = React.useState('')

  // Filter data based on search query
  const filteredData = React.useMemo(() => {
    if (!searchQuery || searchKeys.length === 0) return data

    const query = searchQuery.toLowerCase()
    return data.filter((item) =>
      searchKeys.some((key) => {
        const value = item[key]
        if (typeof value === 'string') {
          return value.toLowerCase().includes(query)
        }
        if (typeof value === 'number') {
          return value.toString().includes(query)
        }
        return false
      })
    )
  }, [data, searchQuery, searchKeys])

  // Sort data
  const sortedData = React.useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn as keyof T]
      const bVal = b[sortColumn as keyof T]

      if (aVal === bVal) return 0
      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      const comparison = aVal < bVal ? -1 : 1
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [filteredData, sortColumn, sortDirection])

  // Paginate data
  const totalPages = Math.ceil(sortedData.length / pageSize)
  const paginatedData = React.useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return sortedData.slice(start, start + pageSize)
  }, [sortedData, currentPage, pageSize])

  // Reset page when search changes
  React.useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery])

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  const handleSelectAll = () => {
    if (!onSelectionChange) return

    const allIds = paginatedData.map(getRowId)
    const allSelected = allIds.every((id) => selectedIds.has(id))

    if (allSelected) {
      const newSelected = new Set(selectedIds)
      allIds.forEach((id) => newSelected.delete(id))
      onSelectionChange(newSelected)
    } else {
      const newSelected = new Set(selectedIds)
      allIds.forEach((id) => newSelected.add(id))
      onSelectionChange(newSelected)
    }
  }

  const handleSelectRow = (item: T) => {
    if (!onSelectionChange) return

    const id = getRowId(item)
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    onSelectionChange(newSelected)
  }

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) {
      return <ChevronsUpDown className="h-4 w-4 text-gray-400" />
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="h-4 w-4 text-primary-600" />
    ) : (
      <ChevronDown className="h-4 w-4 text-primary-600" />
    )
  }

  const allPageSelected =
    paginatedData.length > 0 && paginatedData.every((item) => selectedIds.has(getRowId(item)))

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Search */}
      {searchable && (
        <div className="relative">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label={searchPlaceholder}
            className="w-full max-w-sm px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200" role="region" aria-label="Data table">
        <table className="min-w-full divide-y divide-gray-200" role="grid">
          <thead className="bg-gray-50">
            <tr>
              {selectable && (
                <th className="px-4 py-3 w-12" scope="col">
                  <input
                    type="checkbox"
                    checked={allPageSelected}
                    onChange={handleSelectAll}
                    aria-label="Select all rows on this page"
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  scope="col"
                  aria-sort={
                    sortColumn === String(column.key)
                      ? sortDirection === 'asc' ? 'ascending' : 'descending'
                      : undefined
                  }
                  className={clsx(
                    'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                    column.sortable && 'cursor-pointer hover:bg-gray-100 select-none',
                    column.className
                  )}
                  onClick={() => column.sortable && handleSort(String(column.key))}
                  onKeyDown={(e) => {
                    if (column.sortable && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault()
                      handleSort(String(column.key))
                    }
                  }}
                  tabIndex={column.sortable ? 0 : undefined}
                  role={column.sortable ? 'columnheader button' : 'columnheader'}
                >
                  <div className="flex items-center gap-1">
                    {column.header}
                    {column.sortable && getSortIcon(String(column.key))}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((item, index) => (
                <tr
                  key={getRowId(item)}
                  className={clsx(
                    'transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-gray-50',
                    selectedIds.has(getRowId(item)) && 'bg-primary-50'
                  )}
                  onClick={() => onRowClick?.(item)}
                >
                  {selectable && (
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(getRowId(item))}
                        onChange={() => handleSelectRow(item)}
                        aria-label={`Select row ${index + 1}`}
                        className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                    </td>
                  )}
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className={clsx('px-4 py-3 text-sm text-gray-900', column.className)}
                    >
                      {column.render
                        ? column.render(item, index)
                        : String(item[column.key as keyof T] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="flex items-center justify-between" aria-label="Table pagination">
          <p className="text-sm text-gray-500" aria-live="polite">
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (currentPage <= 3) {
                  pageNum = i + 1
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = currentPage - 2 + i
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    aria-label={`Page ${pageNum}`}
                    aria-current={currentPage === pageNum ? 'page' : undefined}
                    className={clsx(
                      'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                      currentPage === pageNum
                        ? 'bg-primary-600 text-white'
                        : 'hover:bg-gray-100 text-gray-700'
                    )}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </nav>
      )}
    </div>
  )
}
