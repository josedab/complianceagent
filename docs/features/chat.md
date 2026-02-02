# Compliance Copilot Chat

The Compliance Copilot Chat provides an intelligent, context-aware conversational interface for compliance questions, code analysis, and regulatory guidance.

## Overview

The chat assistant combines:
- **RAG (Retrieval-Augmented Generation)** for grounded, accurate responses
- **Conversation memory** for contextual multi-turn discussions
- **Action triggers** for chat-to-action workflows
- **Streaming responses** for real-time interaction

## Features

### Context-Aware Conversations

The assistant maintains conversation context and retrieves relevant information:

**Example conversation:**
- User: "What are GDPR requirements for data deletion?"
- Assistant: "GDPR Article 17 establishes the 'right to erasure'..." (with citations)
- User: "How does our codebase handle this?"
- Assistant: "Your UserService in user_service.py has a delete_user_data() method..."

### Multi-Source RAG Pipeline

The RAG system retrieves context from multiple sources:

1. **Regulations**: Full text and requirements from 100+ frameworks
2. **Codebase Mappings**: How your code maps to requirements
3. **Compliance Policies**: Your organization-specific policies
4. **Audit History**: Past decisions and implementations

### Intent Detection

The system automatically detects query intent:

| Intent | Example | Behavior |
|--------|---------|----------|
| `compliance_status` | "Are we GDPR compliant?" | Queries compliance dashboard data |
| `explanation` | "Explain HIPAA safeguards" | Retrieves regulation text + explains |
| `action` | "Create issue for this" | Triggers action handler |
| `locate` | "Where is consent handled?" | Searches codebase mappings |
| `comparison` | "Compare GDPR vs CCPA" | Multi-regulation analysis |

### Streaming Responses

Real-time SSE streaming for responsive chat:

```javascript
const eventSource = new EventSource('/api/v1/chat/message/stream');
eventSource.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  appendToChat(chunk.content);
};
```

### Action Triggers

Chat can trigger real actions:

```
User: "Create a GitHub issue for the encryption compliance gap"
Assistant: "I'll create an issue for you..."
→ [Creates GitHub issue #234: "HIPAA Compliance: Add encryption for PHI storage"]
```

Available actions:
- Create GitHub issues
- Trigger compliance scans
- Approve team suppressions
- Generate compliance reports

## API Reference

### Send Message

```http
POST /api/v1/chat/message
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "What encryption does HIPAA require?",
    "conversation_id": "optional-existing-id",
    "regulations": ["HIPAA"],
    "include_code_context": true
}
```

**Response:**
```json
{
    "id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "content": "HIPAA requires encryption for Protected Health Information (PHI)...",
    "citations": [
        {
            "source": "HIPAA",
            "title": "45 CFR 164.312(a)(2)(iv)",
            "excerpt": "Implement a mechanism to encrypt and decrypt electronic PHI"
        }
    ],
    "context_used": [
        {"type": "regulation", "id": "hipaa-encryption-req"}
    ],
    "actions": [],
    "model": "gpt-4",
    "input_tokens": 150,
    "output_tokens": 320
}
```

### Stream Message

```http
POST /api/v1/chat/message/stream
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "Explain EU AI Act risk categories"
}
```

**SSE Response:**
```
data: {"type": "start", "conversation_id": "conv-123"}

data: {"type": "chunk", "content": "The EU AI Act classifies "}
data: {"type": "chunk", "content": "AI systems into four risk "}
data: {"type": "chunk", "content": "categories:\n\n1. **Unacceptable..."}

data: {"type": "end", "citations": [...], "usage": {...}}
```

### Analyze Code

```http
POST /api/v1/chat/analyze-code?code=def%20log_user...&language=python
Authorization: Bearer <token>
```

**Response:**
```json
{
    "conversation_id": "conv-uuid",
    "content": "This code has several compliance concerns:\n\n1. **PII Logging (GDPR)**...",
    "citations": [...],
    "actions": [
        {
            "type": "create_issue",
            "label": "Create compliance issue",
            "payload": {...}
        }
    ]
}
```

### Explain Regulation

```http
POST /api/v1/chat/explain-regulation?regulation=GDPR&article=17
Authorization: Bearer <token>
```

### List Conversations

```http
GET /api/v1/chat/conversations
Authorization: Bearer <token>
```

### Get Quick Actions

```http
GET /api/v1/chat/quick-actions
Authorization: Bearer <token>
```

**Response:**
```json
[
    {"label": "Check compliance status", "query": "What is our current compliance status?", "icon": "shield"},
    {"label": "Recent changes", "query": "What regulatory changes affected us this week?", "icon": "bell"},
    {"label": "Pending actions", "query": "What compliance actions need attention?", "icon": "alert"}
]
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chat Frontend  │────▶│  Chat API       │────▶│  Conversation   │
│  (Next.js)      │◀────│  (FastAPI)      │     │  Manager        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  RAG Pipeline   │────▶│  Vector Store   │
                        │  (Retrieval)    │     │  (Embeddings)   │
                        └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Compliance     │
                        │  Assistant      │
                        │  (LLM + Context)│
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Action Handler │────▶ GitHub, Scans, etc.
                        └─────────────────┘
```

## Best Practices

1. **Be specific** - Include regulation names and specific scenarios for better answers
2. **Use conversations** - Build on previous context rather than starting fresh
3. **Leverage actions** - Let the assistant create issues and trigger scans
4. **Review citations** - Always verify cited sources for accuracy

## Frontend Integration

### React Hook Example

```typescript
import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

export function useComplianceChat(conversationId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      });
      return response.json();
    },
    onSuccess: (data) => {
      setMessages(prev => [...prev, data]);
    },
  });

  return { messages, sendMessage: sendMessage.mutate, isLoading: sendMessage.isPending };
}
```

### Streaming Hook

```typescript
export function useStreamingChat() {
  const [content, setContent] = useState('');
  
  const stream = useCallback(async (message: string) => {
    setContent('');
    const response = await fetch('/api/v1/chat/message/stream', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
      
      for (const line of lines) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'chunk') {
          setContent(prev => prev + data.content);
        }
      }
    }
  }, []);

  return { content, stream };
}
```
