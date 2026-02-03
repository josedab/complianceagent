'use client'

import * as React from 'react'
import { X, Trash2, CheckCircle, Archive, Tag, MoreHorizontal, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'

interface BulkAction {
  id: string
  label: string
  icon: React.ReactNode
  variant?: 'default' | 'danger'
  onClick: (selectedIds: string[]) => void | Promise<void>
}

interface BulkActionsBarProps {
  selectedCount: number
  totalCount: number
  onClearSelection: () => void
  onSelectAll: () => void
  actions: BulkAction[]
  className?: string
}

export function BulkActionsBar({
  selectedCount,
  totalCount,
  onClearSelection,
  onSelectAll,
  actions,
  className,
}: BulkActionsBarProps) {
  const [loadingAction, setLoadingAction] = React.useState<string | null>(null)
  const [showMore, setShowMore] = React.useState(false)
  const moreRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setShowMore(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (selectedCount === 0) return null

  const visibleActions = actions.slice(0, 3)
  const overflowActions = actions.slice(3)

  const handleAction = async (action: BulkAction, ids: string[]) => {
    setLoadingAction(action.id)
    try {
      await action.onClick(ids)
    } finally {
      setLoadingAction(null)
    }
  }

  return (
    <div
      className={clsx(
        'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
        'bg-gray-900 text-white rounded-xl shadow-2xl',
        'px-4 py-3 flex items-center gap-4',
        'animate-in slide-in-from-bottom-full duration-200',
        className
      )}
    >
      {/* Selection info */}
      <div className="flex items-center gap-3 border-r border-gray-700 pr-4">
        <button
          onClick={onClearSelection}
          className="p-1 hover:bg-gray-800 rounded transition-colors"
          title="Clear selection"
        >
          <X className="h-4 w-4" />
        </button>
        <span className="text-sm font-medium">
          {selectedCount} selected
        </span>
        {selectedCount < totalCount && (
          <button
            onClick={onSelectAll}
            className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
          >
            Select all {totalCount}
          </button>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {visibleActions.map((action) => (
          <button
            key={action.id}
            onClick={() => handleAction(action, [])}
            disabled={loadingAction !== null}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              action.variant === 'danger'
                ? 'hover:bg-red-500/20 text-red-400'
                : 'hover:bg-gray-800'
            )}
          >
            {loadingAction === action.id ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              action.icon
            )}
            {action.label}
          </button>
        ))}

        {overflowActions.length > 0 && (
          <div ref={moreRef} className="relative">
            <button
              onClick={() => setShowMore(!showMore)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            {showMore && (
              <div className="absolute bottom-full right-0 mb-2 w-48 bg-gray-800 rounded-lg shadow-lg py-1">
                {overflowActions.map((action) => (
                  <button
                    key={action.id}
                    onClick={() => {
                      handleAction(action, [])
                      setShowMore(false)
                    }}
                    disabled={loadingAction !== null}
                    className={clsx(
                      'w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors',
                      action.variant === 'danger'
                        ? 'hover:bg-red-500/20 text-red-400'
                        : 'hover:bg-gray-700'
                    )}
                  >
                    {loadingAction === action.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      action.icon
                    )}
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Predefined actions factory
export const bulkActionPresets = {
  delete: (onDelete: (ids: string[]) => void | Promise<void>): BulkAction => ({
    id: 'delete',
    label: 'Delete',
    icon: <Trash2 className="h-4 w-4" />,
    variant: 'danger',
    onClick: onDelete,
  }),

  approve: (onApprove: (ids: string[]) => void | Promise<void>): BulkAction => ({
    id: 'approve',
    label: 'Approve',
    icon: <CheckCircle className="h-4 w-4" />,
    onClick: onApprove,
  }),

  archive: (onArchive: (ids: string[]) => void | Promise<void>): BulkAction => ({
    id: 'archive',
    label: 'Archive',
    icon: <Archive className="h-4 w-4" />,
    onClick: onArchive,
  }),

  tag: (onTag: (ids: string[]) => void | Promise<void>): BulkAction => ({
    id: 'tag',
    label: 'Add Tag',
    icon: <Tag className="h-4 w-4" />,
    onClick: onTag,
  }),
}

// Hook for managing bulk selection state
export function useBulkSelection<T extends { id: string }>(
  items: T[],
  getItemId: (item: T) => string = (item) => item.id
) {
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set())

  const toggleItem = React.useCallback((item: T) => {
    const id = getItemId(item)
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [getItemId])

  const selectAll = React.useCallback(() => {
    setSelectedIds(new Set(items.map(getItemId)))
  }, [items, getItemId])

  const clearSelection = React.useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  const isSelected = React.useCallback(
    (item: T) => selectedIds.has(getItemId(item)),
    [selectedIds, getItemId]
  )

  const selectedItems = React.useMemo(
    () => items.filter((item) => selectedIds.has(getItemId(item))),
    [items, selectedIds, getItemId]
  )

  return {
    selectedIds,
    selectedItems,
    selectedCount: selectedIds.size,
    toggleItem,
    selectAll,
    clearSelection,
    isSelected,
    setSelectedIds,
  }
}
