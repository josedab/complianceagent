'use client'

import * as React from 'react'
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
  type UniqueIdentifier,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  horizontalListSortingStrategy,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { clsx } from 'clsx'
import { GripVertical } from 'lucide-react'

type SortingStrategy = 'vertical' | 'horizontal' | 'grid'

interface DragDropListProps<T extends { id: string }> {
  items: T[]
  onReorder: (items: T[]) => void
  renderItem: (item: T, isDragging: boolean) => React.ReactNode
  strategy?: SortingStrategy
  className?: string
  itemClassName?: string
  showDragHandle?: boolean
  disabled?: boolean
}

// Hook for sortable item functionality
function useSortableItem(id: string, disabled?: boolean) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id, disabled })

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: disabled ? 'default' : 'grab',
  }

  return {
    ref: setNodeRef,
    style,
    attributes,
    listeners,
    isDragging,
  }
}

// Sortable item wrapper component
interface SortableItemProps {
  id: string
  children: React.ReactNode
  className?: string
  showDragHandle?: boolean
  disabled?: boolean
}

export function SortableItem({
  id,
  children,
  className,
  showDragHandle = true,
  disabled = false,
}: SortableItemProps) {
  const { ref, style, attributes, listeners, isDragging } = useSortableItem(id, disabled)

  return (
    <div
      ref={ref}
      style={style}
      className={clsx(
        'relative group',
        isDragging && 'z-10 shadow-lg',
        className
      )}
    >
      {showDragHandle && !disabled ? (
        <div className="flex items-center gap-2">
          <button
            {...attributes}
            {...listeners}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-grab active:cursor-grabbing touch-none"
            aria-label="Drag handle"
          >
            <GripVertical className="h-4 w-4" />
          </button>
          <div className="flex-1">{children}</div>
        </div>
      ) : (
        <div {...attributes} {...listeners}>
          {children}
        </div>
      )}
    </div>
  )
}

// Main drag-drop list component
export function DragDropList<T extends { id: string }>({
  items,
  onReorder,
  renderItem,
  strategy = 'vertical',
  className,
  itemClassName,
  showDragHandle = true,
  disabled = false,
}: DragDropListProps<T>) {
  const [activeId, setActiveId] = React.useState<UniqueIdentifier | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const sortingStrategy = React.useMemo(() => {
    switch (strategy) {
      case 'horizontal':
        return horizontalListSortingStrategy
      case 'grid':
        return rectSortingStrategy
      default:
        return verticalListSortingStrategy
    }
  }, [strategy])

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveId(null)
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => item.id === active.id)
      const newIndex = items.findIndex((item) => item.id === over.id)
      const newItems = arrayMove(items, oldIndex, newIndex)
      onReorder(newItems)
    }
  }

  const activeItem = activeId ? items.find((item) => item.id === activeId) : null

  const containerClass = clsx(
    strategy === 'horizontal' && 'flex flex-row gap-2',
    strategy === 'grid' && 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4',
    strategy === 'vertical' && 'flex flex-col gap-2',
    className
  )

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={items.map((i) => i.id)} strategy={sortingStrategy}>
        <div className={containerClass}>
          {items.map((item) => (
            <SortableItem
              key={item.id}
              id={item.id}
              className={itemClassName}
              showDragHandle={showDragHandle}
              disabled={disabled}
            >
              {renderItem(item, item.id === activeId)}
            </SortableItem>
          ))}
        </div>
      </SortableContext>

      {/* Drag overlay for better visual feedback */}
      <DragOverlay>
        {activeItem ? (
          <div className="opacity-90 shadow-xl">
            {renderItem(activeItem, true)}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}

// Pre-built draggable card component
interface DraggableCardProps {
  id: string
  title: string
  subtitle?: string
  icon?: React.ReactNode
  badge?: React.ReactNode
  actions?: React.ReactNode
  onClick?: () => void
  className?: string
}

export function DraggableCard({
  title,
  subtitle,
  icon,
  badge,
  actions,
  onClick,
  className,
}: DraggableCardProps) {
  return (
    <div
      className={clsx(
        'flex items-center gap-3 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg',
        onClick && 'cursor-pointer hover:border-primary-300 dark:hover:border-primary-600',
        className
      )}
      onClick={onClick}
    >
      {icon && (
        <div className="flex-shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
          {icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-gray-900 dark:text-white truncate">{title}</h4>
          {badge}
        </div>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex-shrink-0">{actions}</div>}
    </div>
  )
}

// Example: Sortable regulations list
interface Regulation {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  priority: number
}

interface SortableRegulationsProps {
  regulations: Regulation[]
  onReorder: (regulations: Regulation[]) => void
  onSelect?: (regulation: Regulation) => void
}

export function SortableRegulations({
  regulations,
  onReorder,
  onSelect,
}: SortableRegulationsProps) {
  return (
    <DragDropList
      items={regulations}
      onReorder={onReorder}
      strategy="vertical"
      className="space-y-2"
      renderItem={(regulation, isDragging) => (
        <DraggableCard
          id={regulation.id}
          title={regulation.name}
          subtitle={regulation.description}
          onClick={() => onSelect?.(regulation)}
          badge={
            <span
              className={clsx(
                'px-2 py-0.5 text-xs rounded-full',
                regulation.status === 'active'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              )}
            >
              {regulation.status}
            </span>
          }
          className={clsx(isDragging && 'ring-2 ring-primary-500')}
        />
      )}
    />
  )
}

// Example: Sortable action items
interface ActionItem {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  repository: string
}

interface SortableActionsProps {
  actions: ActionItem[]
  onReorder: (actions: ActionItem[]) => void
  onSelect?: (action: ActionItem) => void
}

const severityColors: Record<ActionItem['severity'], string> = {
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
}

export function SortableActions({
  actions,
  onReorder,
  onSelect,
}: SortableActionsProps) {
  return (
    <DragDropList
      items={actions}
      onReorder={onReorder}
      strategy="vertical"
      className="space-y-2"
      renderItem={(action, isDragging) => (
        <DraggableCard
          id={action.id}
          title={action.title}
          subtitle={action.repository}
          onClick={() => onSelect?.(action)}
          badge={
            <span className={clsx('px-2 py-0.5 text-xs rounded-full capitalize', severityColors[action.severity])}>
              {action.severity}
            </span>
          }
          className={clsx(isDragging && 'ring-2 ring-primary-500')}
        />
      )}
    />
  )
}

// Kanban-style board for actions
interface KanbanColumn<T extends { id: string }> {
  id: string
  title: string
  items: T[]
}

interface KanbanBoardProps<T extends { id: string }> {
  columns: KanbanColumn<T>[]
  onReorder: (columnId: string, items: T[]) => void
  onMoveItem?: (itemId: string, fromColumn: string, toColumn: string) => void
  renderItem: (item: T) => React.ReactNode
  className?: string
}

export function KanbanBoard<T extends { id: string }>({
  columns,
  onReorder,
  renderItem,
  className,
}: KanbanBoardProps<T>) {
  return (
    <div className={clsx('flex gap-4 overflow-x-auto pb-4', className)}>
      {columns.map((column) => (
        <div
          key={column.id}
          className="flex-shrink-0 w-80 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4"
        >
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center justify-between">
            {column.title}
            <span className="text-sm font-normal text-gray-500">
              {column.items.length}
            </span>
          </h3>
          <DragDropList
            items={column.items}
            onReorder={(items) => onReorder(column.id, items)}
            strategy="vertical"
            className="space-y-2 min-h-[200px]"
            renderItem={(item) => renderItem(item)}
          />
        </div>
      ))}
    </div>
  )
}
