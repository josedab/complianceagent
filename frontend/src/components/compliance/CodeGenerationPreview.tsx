'use client'

import { useState } from 'react'
import { Code, Copy, Check, ChevronDown, ChevronRight, FileCode, AlertTriangle, CheckCircle } from 'lucide-react'

interface CodeFile {
  path: string
  content: string
  language: string
  operation: 'create' | 'modify' | 'delete'
  diff?: string
}

interface GeneratedCode {
  files: CodeFile[]
  tests?: CodeFile[]
  documentation?: string
  pr_suggestion?: {
    title: string
    body: string
  }
  compliance_notes?: string[]
  confidence: number
  warnings?: string[]
}

interface CodeGenerationPreviewProps {
  generatedCode: GeneratedCode
  requirementTitle?: string
  onApprove?: () => void
  onReject?: () => void
  loading?: boolean
}

export function CodeGenerationPreview({
  generatedCode,
  requirementTitle,
  onApprove,
  onReject,
  loading = false,
}: CodeGenerationPreviewProps) {
  const [activeTab, setActiveTab] = useState<'files' | 'tests' | 'docs'>('files')
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set())
  const [copiedFile, setCopiedFile] = useState<string | null>(null)

  const toggleFile = (path: string) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFiles(newExpanded)
  }

  const copyToClipboard = async (content: string, path: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedFile(path)
    setTimeout(() => setCopiedFile(null), 2000)
  }

  const getLanguageClass = (language: string): string => {
    const languageMap: Record<string, string> = {
      python: 'language-python',
      typescript: 'language-typescript',
      javascript: 'language-javascript',
      java: 'language-java',
      go: 'language-go',
      rust: 'language-rust',
      sql: 'language-sql',
      yaml: 'language-yaml',
      json: 'language-json',
    }
    return languageMap[language.toLowerCase()] || 'language-plaintext'
  }

  const getOperationBadge = (operation: CodeFile['operation']) => {
    switch (operation) {
      case 'create':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">New</span>
      case 'modify':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700">Modified</span>
      case 'delete':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700">Deleted</span>
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Code className="h-5 w-5 text-blue-600" />
              Generated Code Preview
            </h3>
            {requirementTitle && (
              <p className="text-sm text-gray-500 mt-1">For requirement: {requirementTitle}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-sm">
              <span className="text-gray-500">Confidence:</span>
              <span className={`font-medium ${
                generatedCode.confidence >= 0.8 ? 'text-green-600' :
                generatedCode.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {Math.round(generatedCode.confidence * 100)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {generatedCode.warnings && generatedCode.warnings.length > 0 && (
        <div className="px-6 py-3 bg-yellow-50 border-b border-yellow-100">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">Warnings</p>
              <ul className="text-sm text-yellow-700 mt-1 space-y-1">
                {generatedCode.warnings.map((warning, i) => (
                  <li key={i}>• {warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex px-6">
          <button
            onClick={() => setActiveTab('files')}
            className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px ${
              activeTab === 'files'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Files ({generatedCode.files.length})
          </button>
          {generatedCode.tests && generatedCode.tests.length > 0 && (
            <button
              onClick={() => setActiveTab('tests')}
              className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px ${
                activeTab === 'tests'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Tests ({generatedCode.tests.length})
            </button>
          )}
          {generatedCode.documentation && (
            <button
              onClick={() => setActiveTab('docs')}
              className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px ${
                activeTab === 'docs'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Documentation
            </button>
          )}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'files' && (
          <div className="space-y-3">
            {generatedCode.files.map((file) => (
              <div key={file.path} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleFile(file.path)}
                  className="w-full px-4 py-3 bg-gray-50 flex items-center justify-between hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedFiles.has(file.path) ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                    <FileCode className="h-4 w-4 text-gray-500" />
                    <span className="font-mono text-sm text-gray-700">{file.path}</span>
                    {getOperationBadge(file.operation)}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      copyToClipboard(file.content, file.path)
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    title="Copy to clipboard"
                  >
                    {copiedFile === file.path ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </button>
                {expandedFiles.has(file.path) && (
                  <div className="border-t border-gray-200">
                    <pre className={`p-4 bg-gray-900 text-gray-100 text-sm overflow-x-auto ${getLanguageClass(file.language)}`}>
                      <code>{file.content}</code>
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'tests' && generatedCode.tests && (
          <div className="space-y-3">
            {generatedCode.tests.map((file) => (
              <div key={file.path} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleFile(file.path)}
                  className="w-full px-4 py-3 bg-gray-50 flex items-center justify-between hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedFiles.has(file.path) ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                    <FileCode className="h-4 w-4 text-green-500" />
                    <span className="font-mono text-sm text-gray-700">{file.path}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      copyToClipboard(file.content, file.path)
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    title="Copy to clipboard"
                  >
                    {copiedFile === file.path ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </button>
                {expandedFiles.has(file.path) && (
                  <div className="border-t border-gray-200">
                    <pre className={`p-4 bg-gray-900 text-gray-100 text-sm overflow-x-auto ${getLanguageClass(file.language)}`}>
                      <code>{file.content}</code>
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'docs' && generatedCode.documentation && (
          <div className="prose prose-sm max-w-none">
            <div className="p-4 bg-gray-50 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">
                {generatedCode.documentation}
              </pre>
            </div>
          </div>
        )}

        {/* Compliance Notes */}
        {generatedCode.compliance_notes && generatedCode.compliance_notes.length > 0 && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 flex items-center gap-2 mb-2">
              <CheckCircle className="h-4 w-4" />
              Compliance Notes
            </h4>
            <ul className="text-sm text-blue-800 space-y-1">
              {generatedCode.compliance_notes.map((note, i) => (
                <li key={i}>• {note}</li>
              ))}
            </ul>
          </div>
        )}

        {/* PR Suggestion */}
        {generatedCode.pr_suggestion && (
          <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-900">Pull Request Suggestion</h4>
            </div>
            <div className="p-4">
              <div className="mb-3">
                <p className="text-xs text-gray-500 mb-1">Title</p>
                <p className="text-sm font-medium text-gray-900">{generatedCode.pr_suggestion.title}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Description</p>
                <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded whitespace-pre-wrap">
                  {generatedCode.pr_suggestion.body}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      {(onApprove || onReject) && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
          {onReject && (
            <button
              onClick={onReject}
              disabled={loading}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              Reject
            </button>
          )}
          {onApprove && (
            <button
              onClick={onApprove}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating PR...' : 'Approve & Create PR'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default CodeGenerationPreview
