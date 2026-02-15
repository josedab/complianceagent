'use client'

import { useState } from 'react'
import { Code, Shield, AlertCircle, CheckCircle, Info, Send } from 'lucide-react'

interface Suggestion {
  id: string
  lineNumber: number
  severity: 'error' | 'warning' | 'info' | 'hint'
  ruleId: string
  regulation: string
  article: string
  message: string
  explanation: string
  suggestedFix: string
  originalCode: string
  confidence: number
}

const severityConfig = {
  error: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200' },
  warning: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' },
  info: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' },
  hint: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50 border-green-200' },
}

const SAMPLE_CODE = `from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

@app.route('/api/users/<user_id>')
def get_user(user_id):
    user = db.get_user(user_id)
    # Return user data including email and phone
    email = user.email
    phone = user.phone_number
    logging.info(f"User retrieved: {user.name}, email={email}")
    return jsonify({
        "name": user.name,
        "email": email,
        "ssn": user.ssn,
        "credit_card": user.card_number
    })`

const MOCK_SUGGESTIONS: Suggestion[] = [
  { id: '1', lineNumber: 13, severity: 'warning', ruleId: 'GDPR-LOG-002', regulation: 'GDPR', article: 'Art. 5(1)(f)',
    message: 'Potential PII in log output', explanation: 'Logging user email violates GDPR data minimization.',
    suggestedFix: 'Use structured logging with PII redaction', originalCode: 'logging.info(f"User retrieved: {user.name}, email={email}")', confidence: 0.92 },
  { id: '2', lineNumber: 17, severity: 'error', ruleId: 'GDPR-PII-001', regulation: 'GDPR', article: 'Art. 5(1)(c)',
    message: 'PII detected without masking or encryption', explanation: 'SSN is exposed in API response without masking.',
    suggestedFix: 'Apply data masking: mask_pii(value)', originalCode: '"ssn": user.ssn', confidence: 0.95 },
  { id: '3', lineNumber: 18, severity: 'error', ruleId: 'PCI-CARD-001', regulation: 'PCI-DSS', article: 'Req. 3.4',
    message: 'Cardholder data without tokenization', explanation: 'Card numbers must be tokenized or encrypted per PCI-DSS.',
    suggestedFix: 'Replace with tokenized reference: tokenize(card_number)', originalCode: '"credit_card": user.card_number', confidence: 0.97 },
]

export default function PairProgrammingDashboard() {
  const [code, setCode] = useState(SAMPLE_CODE)
  const [suggestions] = useState(MOCK_SUGGESTIONS)
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([
    { role: 'assistant', content: 'I\'m your compliance copilot. I\'ll analyze your code for regulatory violations in real-time. Try editing the code on the left!' },
  ])
  const [chatInput, setChatInput] = useState('')

  const handleSend = () => {
    if (!chatInput.trim()) return
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput },
      { role: 'assistant', content: `Good question about "${chatInput}". Under GDPR Article 5(1)(c), you should apply data minimization principles. Only collect and process PII that is strictly necessary for the stated purpose.` },
    ])
    setChatInput('')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Code className="h-7 w-7 text-green-600" /> Compliance Pair Programming</h1>
        <p className="text-gray-500 mt-1">Real-time AI compliance assistant as you code</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Code Editor */}
        <div className="bg-gray-900 rounded-lg overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-gray-400 text-sm">
            <Code className="h-4 w-4" /> src/api/users.py
            <span className="ml-auto text-xs">{suggestions.length} issues found</span>
          </div>
          <textarea value={code} onChange={e => setCode(e.target.value)}
            className="w-full h-96 bg-gray-900 text-green-400 font-mono text-sm p-4 resize-none focus:outline-none"
            spellCheck={false} />
        </div>

        {/* Chat + Suggestions */}
        <div className="flex flex-col gap-4">
          {/* Suggestions */}
          <div className="bg-white rounded-lg border flex-1 overflow-auto max-h-64">
            <div className="p-3 border-b font-medium text-sm flex items-center gap-2"><Shield className="h-4 w-4 text-blue-600" /> Compliance Suggestions</div>
            <div className="divide-y">
              {suggestions.map(s => {
                const cfg = severityConfig[s.severity]
                const Icon = cfg.icon
                return (
                  <div key={s.id} className={`p-3 ${cfg.bg} border-l-4`}>
                    <div className="flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${cfg.color}`} />
                      <span className="font-medium text-sm">{s.ruleId}</span>
                      <span className="text-xs text-gray-500">{s.regulation} {s.article}</span>
                      <span className="text-xs text-gray-400 ml-auto">Line {s.lineNumber} · {(s.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm mt-1">{s.message}</p>
                    <div className="mt-1 text-xs text-gray-600">Fix: <code className="bg-white px-1 rounded">{s.suggestedFix}</code></div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Chat */}
          <div className="bg-white rounded-lg border flex-1 flex flex-col">
            <div className="p-3 border-b font-medium text-sm">💬 Ask your Compliance Copilot</div>
            <div className="flex-1 p-3 space-y-2 overflow-auto max-h-48">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`text-sm p-2 rounded ${msg.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-gray-50 mr-8'}`}>
                  {msg.content}
                </div>
              ))}
            </div>
            <div className="p-3 border-t flex gap-2">
              <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Ask about regulations..." className="flex-1 text-sm border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-green-500" />
              <button onClick={handleSend} className="p-1.5 bg-green-600 text-white rounded hover:bg-green-700"><Send className="h-4 w-4" /></button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
