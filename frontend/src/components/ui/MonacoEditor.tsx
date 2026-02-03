'use client'

import * as React from 'react'
import dynamic from 'next/dynamic'
import { clsx } from 'clsx'
import { Loader2, Copy, Check, Maximize2, Minimize2, RotateCcw } from 'lucide-react'

// Dynamic import for Monaco to avoid SSR issues
const Editor = dynamic(() => import('@monaco-editor/react').then((mod) => mod.default), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
      <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
    </div>
  ),
})

type Language =
  | 'javascript'
  | 'typescript'
  | 'python'
  | 'java'
  | 'go'
  | 'json'
  | 'yaml'
  | 'markdown'
  | 'html'
  | 'css'
  | 'sql'
  | 'shell'

interface MonacoEditorProps {
  value: string
  onChange?: (value: string | undefined) => void
  language?: Language
  theme?: 'light' | 'dark' | 'auto'
  height?: string | number
  readOnly?: boolean
  showLineNumbers?: boolean
  showMinimap?: boolean
  wordWrap?: 'on' | 'off' | 'wordWrapColumn' | 'bounded'
  fontSize?: number
  tabSize?: number
  className?: string
  onSave?: (value: string) => void
  showToolbar?: boolean
  filename?: string
}

// Map file extensions to Monaco languages
export function getLanguageFromFilename(filename: string): Language {
  const ext = filename.split('.').pop()?.toLowerCase()
  const mapping: Record<string, Language> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    py: 'python',
    java: 'java',
    go: 'go',
    json: 'json',
    yml: 'yaml',
    yaml: 'yaml',
    md: 'markdown',
    html: 'html',
    htm: 'html',
    css: 'css',
    scss: 'css',
    sql: 'sql',
    sh: 'shell',
    bash: 'shell',
    zsh: 'shell',
  }
  return mapping[ext || ''] || 'javascript'
}

export function MonacoEditor({
  value,
  onChange,
  language = 'javascript',
  theme = 'auto',
  height = '400px',
  readOnly = false,
  showLineNumbers = true,
  showMinimap = false,
  wordWrap = 'on',
  fontSize = 14,
  tabSize = 2,
  className,
  onSave,
  showToolbar = true,
  filename,
}: MonacoEditorProps) {
  const [copied, setCopied] = React.useState(false)
  const [isFullscreen, setIsFullscreen] = React.useState(false)
  const [internalValue, setInternalValue] = React.useState(value)
  const editorRef = React.useRef<unknown>(null)
  const containerRef = React.useRef<HTMLDivElement>(null)

  // Detect system theme
  const [systemTheme, setSystemTheme] = React.useState<'light' | 'dark'>('dark')
  
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light')
    
    const handler = (e: MediaQueryListEvent) => setSystemTheme(e.matches ? 'dark' : 'light')
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  const resolvedTheme = theme === 'auto' ? systemTheme : theme
  const monacoTheme = resolvedTheme === 'dark' ? 'vs-dark' : 'light'

  // Sync external value changes
  React.useEffect(() => {
    setInternalValue(value)
  }, [value])

  const handleEditorChange = (newValue: string | undefined) => {
    setInternalValue(newValue || '')
    onChange?.(newValue)
  }

  const handleEditorMount = (editor: unknown) => {
    editorRef.current = editor
    
    // Add save shortcut
    const ed = editor as { addCommand: (keyCode: number, handler: () => void) => void }
    // Monaco KeyMod.CtrlCmd | KeyCode.KeyS = 2048 | 49 = 2097
    ed.addCommand(2097, () => {
      onSave?.(internalValue)
    })
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(internalValue)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleReset = () => {
    setInternalValue(value)
    onChange?.(value)
  }

  const toggleFullscreen = () => {
    if (!containerRef.current) return
    
    if (!isFullscreen) {
      containerRef.current.requestFullscreen?.()
    } else {
      document.exitFullscreen?.()
    }
  }

  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  const detectedLanguage = filename ? getLanguageFromFilename(filename) : language

  return (
    <div
      ref={containerRef}
      className={clsx(
        'border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden',
        isFullscreen && 'fixed inset-0 z-50 rounded-none',
        className
      )}
    >
      {/* Toolbar */}
      {showToolbar && (
        <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            {filename && (
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {filename}
              </span>
            )}
            <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
              {detectedLanguage}
            </span>
            {readOnly && (
              <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded">
                Read Only
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            {!readOnly && internalValue !== value && (
              <button
                onClick={handleReset}
                className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                title="Reset changes"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            )}
            <button
              onClick={handleCopy}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
              title="Copy code"
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </button>
            <button
              onClick={toggleFullscreen}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}
      
      {/* Editor */}
      <Editor
        height={isFullscreen ? 'calc(100vh - 48px)' : height}
        language={detectedLanguage}
        value={internalValue}
        onChange={handleEditorChange}
        onMount={handleEditorMount}
        theme={monacoTheme}
        options={{
          readOnly,
          lineNumbers: showLineNumbers ? 'on' : 'off',
          minimap: { enabled: showMinimap },
          wordWrap,
          fontSize,
          tabSize,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 12, bottom: 12 },
          folding: true,
          foldingHighlight: true,
          bracketPairColorization: { enabled: true },
          guides: {
            bracketPairs: true,
            indentation: true,
          },
          suggest: {
            showKeywords: true,
            showSnippets: true,
          },
          quickSuggestions: !readOnly,
          parameterHints: { enabled: !readOnly },
          formatOnPaste: !readOnly,
          formatOnType: !readOnly,
        }}
      />
    </div>
  )
}

// Diff Editor for comparing two versions
const DiffEditor = dynamic(
  () => import('@monaco-editor/react').then((mod) => mod.DiffEditor),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    ),
  }
)

interface MonacoDiffEditorProps {
  original: string
  modified: string
  language?: Language
  theme?: 'light' | 'dark' | 'auto'
  height?: string | number
  className?: string
  originalFilename?: string
  modifiedFilename?: string
}

export function MonacoDiffEditor({
  original,
  modified,
  language = 'javascript',
  theme = 'auto',
  height = '400px',
  className,
  originalFilename,
  modifiedFilename,
}: MonacoDiffEditorProps) {
  const [systemTheme, setSystemTheme] = React.useState<'light' | 'dark'>('dark')
  
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light')
    
    const handler = (e: MediaQueryListEvent) => setSystemTheme(e.matches ? 'dark' : 'light')
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  const resolvedTheme = theme === 'auto' ? systemTheme : theme
  const monacoTheme = resolvedTheme === 'dark' ? 'vs-dark' : 'light'

  return (
    <div
      className={clsx(
        'border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-red-600 dark:text-red-400">
            {originalFilename || 'Original'}
          </span>
          <span className="text-gray-400">→</span>
          <span className="text-green-600 dark:text-green-400">
            {modifiedFilename || 'Modified'}
          </span>
        </div>
        <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
          {language}
        </span>
      </div>
      
      <DiffEditor
        height={height}
        language={language}
        original={original}
        modified={modified}
        theme={monacoTheme}
        options={{
          readOnly: true,
          renderSideBySide: true,
          lineNumbers: 'on',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  )
}
