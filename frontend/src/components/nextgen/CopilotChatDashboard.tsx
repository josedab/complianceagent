'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, User, Bot, RefreshCw, Sparkles, ChevronDown } from 'lucide-react'

type Persona = 'developer' | 'cco' | 'auditor' | 'legal' | 'executive'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: string[]
}

const PERSONA_CONFIG: Record<Persona, { label: string; color: string; description: string }> = {
  developer: { label: 'Developer', color: 'bg-blue-100 text-blue-700', description: 'Code-level compliance insights' },
  cco: { label: 'Compliance Officer', color: 'bg-purple-100 text-purple-700', description: 'Regulatory monitoring & reporting' },
  auditor: { label: 'Auditor', color: 'bg-green-100 text-green-700', description: 'Evidence & audit trail queries' },
  legal: { label: 'Legal Counsel', color: 'bg-amber-100 text-amber-700', description: 'Legal interpretation & risk' },
  executive: { label: 'Executive', color: 'bg-red-100 text-red-700', description: 'Strategic compliance overview' },
}

const SUGGESTED_QUERIES: Record<Persona, string[]> = {
  developer: [
    'Is this API endpoint GDPR compliant?',
    'Show me HIPAA encryption requirements for PHI data',
    'What PCI-DSS controls apply to our payment module?',
    'Generate a consent banner implementation',
  ],
  cco: [
    'What regulations changed this week?',
    'Show our compliance posture across all frameworks',
    'Which repositories have the most compliance gaps?',
    'Generate a board-level compliance summary',
  ],
  auditor: [
    'Show evidence for SOC 2 CC6.1 control',
    'List all access control audit entries',
    'Generate ISO 27001 audit readiness report',
    'Which controls are missing evidence?',
  ],
  legal: [
    'How does CCPA differ from GDPR for consent?',
    'What are the EU AI Act obligations for our system?',
    'Summarize cross-border data transfer requirements',
    'What are the penalties for HIPAA non-compliance?',
  ],
  executive: [
    'What is our overall compliance risk score?',
    'How much are we spending on compliance?',
    'What are the top 3 compliance priorities?',
    'Show regulatory forecast for next quarter',
  ],
}

const MOCK_RESPONSES: Record<string, string> = {
  'Is this API endpoint GDPR compliant?': `Based on analysis of the current endpoint, there are **2 compliance gaps**:

1. **Missing Data Minimization** (GDPR Art. 5(1)(c)) — The endpoint collects \`user_agent\` and \`ip_address\` without necessity justification. Recommendation: Add a data minimization filter.

2. **No Consent Verification** (GDPR Art. 6) — The endpoint processes personal data without verifying consent status. Add a consent check middleware.

**Quick Fix Available:** I can generate a GDPR-compliant wrapper for this endpoint. Would you like me to create a PR?`,
  'default': `I've analyzed your query against the regulatory knowledge base. Here's what I found:

Based on the current compliance framework mappings and your organization's regulatory obligations, there are several relevant considerations. The analysis covers applicable regulations, code-level impacts, and recommended remediation steps.

Would you like me to drill deeper into any specific area or generate implementation code for the recommendations?`,
}

export default function CopilotChatDashboard() {
  const [persona, setPersona] = useState<Persona>('developer')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I\'m your Compliance Copilot. I can help you with regulatory questions, code compliance checks, and audit preparation. Select a persona above to customize my responses for your role.\n\nWhat would you like to know?',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [showPersonaDropdown, setShowPersonaDropdown] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const query = text || input
    if (!query.trim() || isStreaming) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsStreaming(true)

    // Simulate streaming response
    const response = MOCK_RESPONSES[query] || MOCK_RESPONSES['default']
    const assistantMsg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      sources: ['GDPR Art. 5-6', 'Internal Policy P-001'],
    }

    setMessages(prev => [...prev, assistantMsg])

    // Simulate streaming character by character
    for (let i = 0; i <= response.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 8))
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last.role === 'assistant') {
          updated[updated.length - 1] = { ...last, content: response.slice(0, i) }
        }
        return updated
      })
    }

    setIsStreaming(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const pc = PERSONA_CONFIG[persona]

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-indigo-600" />
            Compliance Copilot Chat
          </h1>
          <p className="text-gray-500">AI-powered compliance assistant — context-aware for your role</p>
        </div>

        {/* Persona Selector */}
        <div className="relative">
          <button
            onClick={() => setShowPersonaDropdown(!showPersonaDropdown)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${pc.color}`}
          >
            <User className="h-4 w-4" />
            {pc.label}
            <ChevronDown className="h-3 w-3" />
          </button>
          {showPersonaDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
              {(Object.entries(PERSONA_CONFIG) as [Persona, typeof pc][]).map(([key, config]) => (
                <button
                  key={key}
                  onClick={() => { setPersona(key); setShowPersonaDropdown(false) }}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg ${
                    persona === key ? 'bg-indigo-50' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900">{config.label}</p>
                  <p className="text-xs text-gray-500">{config.description}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                <Bot className="h-5 w-5 text-indigo-600" />
              </div>
            )}
            <div className={`max-w-[70%] rounded-lg px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              {msg.role === 'assistant' && msg.content && msg.sources && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-500">Sources: {msg.sources.join(' · ')}</p>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                <User className="h-5 w-5 text-white" />
              </div>
            )}
          </div>
        ))}
        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Analyzing...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Queries */}
      {messages.length <= 1 && (
        <div className="pb-3">
          <p className="text-xs text-gray-500 mb-2">Suggested questions for {pc.label}:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUERIES[persona].map(q => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs text-gray-700 hover:bg-indigo-50 hover:border-indigo-300"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask a compliance question as ${pc.label}...`}
              rows={1}
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isStreaming}
            className="flex items-center justify-center h-11 w-11 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
