'use client'

import * as React from 'react'
import { Check, Copy, ChevronDown, ChevronRight, FileCode } from 'lucide-react'
import { clsx } from 'clsx'

// Simple syntax highlighting without external dependencies
// Supports: Python, TypeScript, JavaScript, Java, Go, JSON, YAML, Bash

type Language = 'python' | 'typescript' | 'javascript' | 'java' | 'go' | 'json' | 'yaml' | 'bash' | 'text'

interface CodeBlockProps {
  code: string
  language?: Language
  filename?: string
  showLineNumbers?: boolean
  highlightLines?: number[]
  maxHeight?: number
  collapsible?: boolean
  defaultCollapsed?: boolean
  className?: string
}

const languageLabels: Record<Language, string> = {
  python: 'Python',
  typescript: 'TypeScript',
  javascript: 'JavaScript',
  java: 'Java',
  go: 'Go',
  json: 'JSON',
  yaml: 'YAML',
  bash: 'Bash',
  text: 'Text',
}

const languageColors: Record<Language, string> = {
  python: 'bg-blue-500',
  typescript: 'bg-blue-600',
  javascript: 'bg-yellow-500',
  java: 'bg-red-500',
  go: 'bg-cyan-500',
  json: 'bg-gray-500',
  yaml: 'bg-purple-500',
  bash: 'bg-green-500',
  text: 'bg-gray-400',
}

// Token types for highlighting
type TokenType = 'keyword' | 'string' | 'number' | 'comment' | 'function' | 'operator' | 'variable' | 'text'

const tokenColors: Record<TokenType, string> = {
  keyword: 'text-purple-400',
  string: 'text-green-400',
  number: 'text-orange-400',
  comment: 'text-gray-500 italic',
  function: 'text-yellow-300',
  operator: 'text-pink-400',
  variable: 'text-cyan-300',
  text: 'text-gray-200',
}

// Language-specific keywords
const keywords: Record<Language, string[]> = {
  python: ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return', 'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'async', 'await', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'yield', 'raise', 'pass', 'break', 'continue', 'global', 'nonlocal', 'assert', 'del'],
  typescript: ['const', 'let', 'var', 'function', 'class', 'interface', 'type', 'enum', 'if', 'else', 'for', 'while', 'return', 'import', 'export', 'from', 'as', 'try', 'catch', 'finally', 'async', 'await', 'true', 'false', 'null', 'undefined', 'new', 'this', 'super', 'extends', 'implements', 'private', 'public', 'protected', 'static', 'readonly', 'abstract', 'default', 'switch', 'case', 'break', 'continue', 'throw', 'typeof', 'instanceof'],
  javascript: ['const', 'let', 'var', 'function', 'class', 'if', 'else', 'for', 'while', 'return', 'import', 'export', 'from', 'as', 'try', 'catch', 'finally', 'async', 'await', 'true', 'false', 'null', 'undefined', 'new', 'this', 'super', 'extends', 'default', 'switch', 'case', 'break', 'continue', 'throw', 'typeof', 'instanceof'],
  java: ['class', 'interface', 'enum', 'extends', 'implements', 'public', 'private', 'protected', 'static', 'final', 'abstract', 'void', 'int', 'long', 'double', 'float', 'boolean', 'String', 'if', 'else', 'for', 'while', 'do', 'return', 'try', 'catch', 'finally', 'throw', 'throws', 'new', 'this', 'super', 'null', 'true', 'false', 'import', 'package', 'synchronized', 'volatile', 'transient', 'native', 'instanceof', 'switch', 'case', 'default', 'break', 'continue'],
  go: ['func', 'package', 'import', 'var', 'const', 'type', 'struct', 'interface', 'map', 'chan', 'if', 'else', 'for', 'range', 'return', 'switch', 'case', 'default', 'break', 'continue', 'go', 'defer', 'select', 'true', 'false', 'nil', 'make', 'new', 'len', 'cap', 'append', 'copy', 'delete', 'panic', 'recover'],
  json: [],
  yaml: ['true', 'false', 'null', 'yes', 'no'],
  bash: ['if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'do', 'done', 'case', 'esac', 'function', 'return', 'exit', 'export', 'local', 'readonly', 'shift', 'source', 'alias', 'unalias', 'set', 'unset', 'cd', 'echo', 'printf', 'read', 'test'],
  text: [],
}

function tokenize(code: string, language: Language): Array<{ type: TokenType; value: string }> {
  const tokens: Array<{ type: TokenType; value: string }> = []
  const langKeywords = keywords[language] || []
  
  // Simple tokenizer - can be enhanced for more accuracy
  let remaining = code
  
  while (remaining.length > 0) {
    let matched = false
    
    // Comments
    if (language !== 'json' && language !== 'yaml') {
      const singleLineComment = remaining.match(/^(\/\/.*|#.*)/)
      if (singleLineComment) {
        tokens.push({ type: 'comment', value: singleLineComment[0] })
        remaining = remaining.slice(singleLineComment[0].length)
        matched = true
        continue
      }
      
      const multiLineComment = remaining.match(/^\/\*[\s\S]*?\*\//)
      if (multiLineComment) {
        tokens.push({ type: 'comment', value: multiLineComment[0] })
        remaining = remaining.slice(multiLineComment[0].length)
        matched = true
        continue
      }
    }
    
    // Strings (double and single quotes, template literals)
    const string = remaining.match(/^(["'`])(?:(?!\1)[^\\]|\\.)*\1/)
    if (string) {
      tokens.push({ type: 'string', value: string[0] })
      remaining = remaining.slice(string[0].length)
      matched = true
      continue
    }
    
    // Numbers
    const number = remaining.match(/^\b\d+\.?\d*\b/)
    if (number) {
      tokens.push({ type: 'number', value: number[0] })
      remaining = remaining.slice(number[0].length)
      matched = true
      continue
    }
    
    // Keywords and identifiers
    const word = remaining.match(/^[a-zA-Z_][a-zA-Z0-9_]*/)
    if (word) {
      const type = langKeywords.includes(word[0]) ? 'keyword' : 'text'
      tokens.push({ type, value: word[0] })
      remaining = remaining.slice(word[0].length)
      matched = true
      continue
    }
    
    // Operators
    const operator = remaining.match(/^[+\-*/%=<>!&|^~?:]+/)
    if (operator) {
      tokens.push({ type: 'operator', value: operator[0] })
      remaining = remaining.slice(operator[0].length)
      matched = true
      continue
    }
    
    // Default: single character
    if (!matched) {
      tokens.push({ type: 'text', value: remaining[0] })
      remaining = remaining.slice(1)
    }
  }
  
  return tokens
}

function highlightLine(line: string, language: Language): React.ReactNode {
  const tokens = tokenize(line, language)
  
  return tokens.map((token, i) => (
    <span key={i} className={tokenColors[token.type]}>
      {token.value}
    </span>
  ))
}

export function CodeBlock({
  code,
  language = 'text',
  filename,
  showLineNumbers = true,
  highlightLines = [],
  maxHeight,
  collapsible = false,
  defaultCollapsed = false,
  className,
}: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false)
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed)
  
  const lines = code.split('\n')
  const lineCount = lines.length
  const lineNumberWidth = String(lineCount).length
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <div className={clsx('rounded-lg overflow-hidden border border-gray-700', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1 hover:bg-gray-700 rounded"
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              )}
            </button>
          )}
          {filename && (
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-300 font-mono">{filename}</span>
            </div>
          )}
          {!filename && (
            <div className="flex items-center gap-2">
              <div className={clsx('w-2 h-2 rounded-full', languageColors[language])} />
              <span className="text-xs text-gray-400">{languageLabels[language]}</span>
            </div>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-green-400" />
              <span className="text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      
      {/* Code */}
      {!collapsed && (
        <div
          className="overflow-auto bg-gray-900"
          style={{ maxHeight: maxHeight ? `${maxHeight}px` : undefined }}
        >
          <pre className="p-4 text-sm font-mono leading-relaxed">
            {lines.map((line, i) => {
              const lineNum = i + 1
              const isHighlighted = highlightLines.includes(lineNum)
              
              return (
                <div
                  key={i}
                  className={clsx(
                    'flex',
                    isHighlighted && 'bg-yellow-500/10 -mx-4 px-4'
                  )}
                >
                  {showLineNumbers && (
                    <span
                      className="select-none text-gray-600 text-right pr-4"
                      style={{ width: `${lineNumberWidth + 2}ch` }}
                    >
                      {lineNum}
                    </span>
                  )}
                  <code className="flex-1">{highlightLine(line, language)}</code>
                </div>
              )
            })}
          </pre>
        </div>
      )}
      
      {/* Collapsed indicator */}
      {collapsed && (
        <div className="px-4 py-2 bg-gray-900 text-gray-500 text-sm">
          {lineCount} lines hidden
        </div>
      )}
    </div>
  )
}

// Inline code component
export function InlineCode({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <code
      className={clsx(
        'px-1.5 py-0.5 text-sm font-mono bg-gray-100 dark:bg-gray-800 text-pink-600 dark:text-pink-400 rounded',
        className
      )}
    >
      {children}
    </code>
  )
}

// Detect language from filename
export function detectLanguage(filename: string): Language {
  const ext = filename.split('.').pop()?.toLowerCase()
  const extMap: Record<string, Language> = {
    py: 'python',
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    java: 'java',
    go: 'go',
    json: 'json',
    yml: 'yaml',
    yaml: 'yaml',
    sh: 'bash',
    bash: 'bash',
  }
  return extMap[ext || ''] || 'text'
}
