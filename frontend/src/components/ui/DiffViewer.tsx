'use client'

import * as React from 'react'
import { Plus, Minus, FileCode, ChevronDown, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'header'
  content: string
  oldLineNumber?: number
  newLineNumber?: number
}

interface DiffViewerProps {
  diff: string
  filename?: string
  language?: string
  viewMode?: 'unified' | 'split'
  maxHeight?: number
  collapsible?: boolean
  defaultCollapsed?: boolean
  className?: string
}

function parseDiff(diff: string): DiffLine[] {
  const lines = diff.split('\n')
  const result: DiffLine[] = []
  
  let oldLine = 0
  let newLine = 0
  
  for (const line of lines) {
    // Parse diff header to get starting line numbers
    const headerMatch = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/)
    if (headerMatch) {
      oldLine = parseInt(headerMatch[1], 10)
      newLine = parseInt(headerMatch[2], 10)
      result.push({ type: 'header', content: line })
      continue
    }
    
    // Skip file headers
    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('diff ') || line.startsWith('index ')) {
      continue
    }
    
    if (line.startsWith('+')) {
      result.push({
        type: 'added',
        content: line.slice(1),
        newLineNumber: newLine++,
      })
    } else if (line.startsWith('-')) {
      result.push({
        type: 'removed',
        content: line.slice(1),
        oldLineNumber: oldLine++,
      })
    } else if (line.startsWith(' ') || line === '') {
      result.push({
        type: 'unchanged',
        content: line.slice(1) || '',
        oldLineNumber: oldLine++,
        newLineNumber: newLine++,
      })
    }
  }
  
  return result
}

export function DiffViewer({
  diff,
  filename,
  viewMode = 'unified',
  maxHeight,
  collapsible = false,
  defaultCollapsed = false,
  className,
}: DiffViewerProps) {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed)
  const lines = React.useMemo(() => parseDiff(diff), [diff])
  
  const stats = React.useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        if (line.type === 'added') acc.added++
        if (line.type === 'removed') acc.removed++
        return acc
      },
      { added: 0, removed: 0 }
    )
  }, [lines])
  
  return (
    <div className={clsx('rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </button>
          )}
          {filename && (
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-mono text-gray-700 dark:text-gray-300">{filename}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <Plus className="h-3.5 w-3.5" />
            {stats.added}
          </span>
          <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
            <Minus className="h-3.5 w-3.5" />
            {stats.removed}
          </span>
        </div>
      </div>
      
      {/* Diff content */}
      {!collapsed && (
        <div
          className="overflow-auto bg-white dark:bg-gray-900"
          style={{ maxHeight: maxHeight ? `${maxHeight}px` : undefined }}
        >
          {viewMode === 'unified' ? (
            <UnifiedDiff lines={lines} />
          ) : (
            <SplitDiff lines={lines} />
          )}
        </div>
      )}
      
      {collapsed && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 text-gray-500 text-sm">
          {stats.added} additions, {stats.removed} deletions
        </div>
      )}
    </div>
  )
}

function UnifiedDiff({ lines }: { lines: DiffLine[] }) {
  return (
    <pre className="text-sm font-mono">
      {lines.map((line, i) => {
        if (line.type === 'header') {
          return (
            <div
              key={i}
              className="px-4 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-y border-blue-100 dark:border-blue-900/30"
            >
              {line.content}
            </div>
          )
        }
        
        const bgColor = {
          added: 'bg-green-50 dark:bg-green-900/20',
          removed: 'bg-red-50 dark:bg-red-900/20',
          unchanged: '',
        }[line.type]
        
        const textColor = {
          added: 'text-green-700 dark:text-green-300',
          removed: 'text-red-700 dark:text-red-300',
          unchanged: 'text-gray-700 dark:text-gray-300',
        }[line.type]
        
        const symbol = {
          added: '+',
          removed: '-',
          unchanged: ' ',
        }[line.type]
        
        return (
          <div key={i} className={clsx('flex', bgColor)}>
            <span className="w-12 text-right pr-2 text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
              {line.oldLineNumber || ''}
            </span>
            <span className="w-12 text-right pr-2 text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
              {line.newLineNumber || ''}
            </span>
            <span className={clsx('w-5 text-center select-none', textColor)}>
              {symbol}
            </span>
            <code className={clsx('flex-1 pl-1 pr-4', textColor)}>
              {line.content || '\u00A0'}
            </code>
          </div>
        )
      })}
    </pre>
  )
}

function SplitDiff({ lines }: { lines: DiffLine[] }) {
  // Group lines for split view
  const leftLines: DiffLine[] = []
  const rightLines: DiffLine[] = []
  
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    
    if (line.type === 'header') {
      leftLines.push(line)
      rightLines.push(line)
      i++
      continue
    }
    
    if (line.type === 'unchanged') {
      leftLines.push(line)
      rightLines.push(line)
      i++
      continue
    }
    
    // Collect consecutive removed/added lines
    const removed: DiffLine[] = []
    const added: DiffLine[] = []
    
    while (i < lines.length && lines[i].type === 'removed') {
      removed.push(lines[i])
      i++
    }
    while (i < lines.length && lines[i].type === 'added') {
      added.push(lines[i])
      i++
    }
    
    // Pair them up
    const maxLen = Math.max(removed.length, added.length)
    for (let j = 0; j < maxLen; j++) {
      leftLines.push(removed[j] || { type: 'unchanged', content: '', oldLineNumber: undefined })
      rightLines.push(added[j] || { type: 'unchanged', content: '', newLineNumber: undefined })
    }
  }
  
  return (
    <div className="flex">
      <div className="flex-1 border-r border-gray-200 dark:border-gray-700">
        <pre className="text-sm font-mono">
          {leftLines.map((line, i) => (
            <SplitDiffLine key={i} line={line} side="left" />
          ))}
        </pre>
      </div>
      <div className="flex-1">
        <pre className="text-sm font-mono">
          {rightLines.map((line, i) => (
            <SplitDiffLine key={i} line={line} side="right" />
          ))}
        </pre>
      </div>
    </div>
  )
}

function SplitDiffLine({ line, side }: { line: DiffLine; side: 'left' | 'right' }) {
  if (line.type === 'header') {
    return (
      <div className="px-4 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-y border-blue-100 dark:border-blue-900/30">
        {side === 'left' ? line.content : ''}
      </div>
    )
  }
  
  const isRelevant = side === 'left' ? line.type === 'removed' : line.type === 'added'
  const bgColor = isRelevant
    ? side === 'left'
      ? 'bg-red-50 dark:bg-red-900/20'
      : 'bg-green-50 dark:bg-green-900/20'
    : ''
  
  const textColor = isRelevant
    ? side === 'left'
      ? 'text-red-700 dark:text-red-300'
      : 'text-green-700 dark:text-green-300'
    : 'text-gray-700 dark:text-gray-300'
  
  const lineNum = side === 'left' ? line.oldLineNumber : line.newLineNumber
  
  return (
    <div className={clsx('flex', bgColor)}>
      <span className="w-12 text-right pr-2 text-gray-400 select-none border-r border-gray-200 dark:border-gray-700">
        {lineNum || ''}
      </span>
      <code className={clsx('flex-1 pl-2 pr-4', textColor)}>
        {line.content || '\u00A0'}
      </code>
    </div>
  )
}

// Simple diff generator for comparing two strings
export function generateDiff(oldContent: string, newContent: string): string {
  const oldLines = oldContent.split('\n')
  const newLines = newContent.split('\n')
  
  const diff: string[] = ['@@ -1,' + oldLines.length + ' +1,' + newLines.length + ' @@']
  
  // Simple line-by-line diff (for more complex diffs, use a proper diff library)
  const maxLen = Math.max(oldLines.length, newLines.length)
  
  for (let i = 0; i < maxLen; i++) {
    const oldLine = oldLines[i]
    const newLine = newLines[i]
    
    if (oldLine === newLine) {
      if (oldLine !== undefined) {
        diff.push(' ' + oldLine)
      }
    } else {
      if (oldLine !== undefined) {
        diff.push('-' + oldLine)
      }
      if (newLine !== undefined) {
        diff.push('+' + newLine)
      }
    }
  }
  
  return diff.join('\n')
}
