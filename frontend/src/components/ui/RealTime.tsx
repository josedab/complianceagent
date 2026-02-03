'use client'

import * as React from 'react'
import { clsx } from 'clsx'
import { Wifi, WifiOff, RefreshCw } from 'lucide-react'

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface WebSocketMessage<T = unknown> {
  type: string
  payload: T
  timestamp: number
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseWebSocketReturn {
  status: ConnectionStatus
  send: (message: WebSocketMessage) => void
  disconnect: () => void
  reconnect: () => void
  lastMessage: WebSocketMessage | null
}

// WebSocket hook for real-time updates
export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = React.useState<ConnectionStatus>('disconnected')
  const [lastMessage, setLastMessage] = React.useState<WebSocketMessage | null>(null)
  const wsRef = React.useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = React.useRef(0)
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout>()

  const connect = React.useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setStatus('connecting')
    
    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        setStatus('connected')
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(message)
          onMessage?.(message)
        } catch {
          console.error('Failed to parse WebSocket message:', event.data)
        }
      }

      wsRef.current.onclose = () => {
        setStatus('disconnected')
        onDisconnect?.()

        // Auto-reconnect
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval)
        }
      }

      wsRef.current.onerror = (error) => {
        setStatus('error')
        onError?.(error)
      }
    } catch (error) {
      setStatus('error')
      console.error('WebSocket connection error:', error)
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnect, reconnectInterval, maxReconnectAttempts])

  const disconnect = React.useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    reconnectAttemptsRef.current = maxReconnectAttempts // Prevent auto-reconnect
    wsRef.current?.close()
    setStatus('disconnected')
  }, [maxReconnectAttempts])

  const send = React.useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const manualReconnect = React.useCallback(() => {
    reconnectAttemptsRef.current = 0
    disconnect()
    setTimeout(connect, 100)
  }, [connect, disconnect])

  // Auto-connect on mount
  React.useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  return {
    status,
    send,
    disconnect,
    reconnect: manualReconnect,
    lastMessage,
  }
}

// Connection status indicator component
interface ConnectionStatusProps {
  status: ConnectionStatus
  onReconnect?: () => void
  className?: string
  showLabel?: boolean
}

export function ConnectionStatus({
  status,
  onReconnect,
  className,
  showLabel = true,
}: ConnectionStatusProps) {
  const statusConfig: Record<ConnectionStatus, { icon: React.ReactNode; label: string; color: string }> = {
    connecting: {
      icon: <RefreshCw className="h-4 w-4 animate-spin" />,
      label: 'Connecting...',
      color: 'text-yellow-500',
    },
    connected: {
      icon: <Wifi className="h-4 w-4" />,
      label: 'Connected',
      color: 'text-green-500',
    },
    disconnected: {
      icon: <WifiOff className="h-4 w-4" />,
      label: 'Disconnected',
      color: 'text-gray-400',
    },
    error: {
      icon: <WifiOff className="h-4 w-4" />,
      label: 'Connection Error',
      color: 'text-red-500',
    },
  }

  const config = statusConfig[status]

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <span className={config.color}>{config.icon}</span>
      {showLabel && (
        <span className={clsx('text-sm', config.color)}>{config.label}</span>
      )}
      {(status === 'disconnected' || status === 'error') && onReconnect && (
        <button
          onClick={onReconnect}
          className="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
        >
          Reconnect
        </button>
      )}
    </div>
  )
}

// Real-time compliance status types
export interface ComplianceUpdate {
  repositoryId: string
  repositoryName: string
  status: 'scanning' | 'compliant' | 'non-compliant' | 'error'
  score?: number
  issuesFound?: number
  lastScan?: string
}

export interface NotificationUpdate {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  read: boolean
}

// Context for real-time updates
interface RealTimeContextValue {
  status: ConnectionStatus
  complianceUpdates: Map<string, ComplianceUpdate>
  notifications: NotificationUpdate[]
  unreadCount: number
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
  reconnect: () => void
}

const RealTimeContext = React.createContext<RealTimeContextValue | undefined>(undefined)

interface RealTimeProviderProps {
  children: React.ReactNode
  wsUrl?: string
}

export function RealTimeProvider({
  children,
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080/ws',
}: RealTimeProviderProps) {
  const [complianceUpdates, setComplianceUpdates] = React.useState<Map<string, ComplianceUpdate>>(
    new Map()
  )
  const [notifications, setNotifications] = React.useState<NotificationUpdate[]>([])

  const handleMessage = React.useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'compliance_update': {
        const update = message.payload as ComplianceUpdate
        setComplianceUpdates((prev) => {
          const next = new Map(prev)
          next.set(update.repositoryId, update)
          return next
        })
        break
      }
      case 'notification': {
        const notification = message.payload as NotificationUpdate
        setNotifications((prev) => [notification, ...prev].slice(0, 50)) // Keep last 50
        break
      }
      case 'bulk_compliance_update': {
        const updates = message.payload as ComplianceUpdate[]
        setComplianceUpdates((prev) => {
          const next = new Map(prev)
          updates.forEach((update) => next.set(update.repositoryId, update))
          return next
        })
        break
      }
    }
  }, [])

  const { status, reconnect } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    reconnect: true,
    maxReconnectAttempts: 10,
  })

  const unreadCount = React.useMemo(
    () => notifications.filter((n) => !n.read).length,
    [notifications]
  )

  const markNotificationRead = React.useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }, [])

  const clearNotifications = React.useCallback(() => {
    setNotifications([])
  }, [])

  return (
    <RealTimeContext.Provider
      value={{
        status,
        complianceUpdates,
        notifications,
        unreadCount,
        markNotificationRead,
        clearNotifications,
        reconnect,
      }}
    >
      {children}
    </RealTimeContext.Provider>
  )
}

export function useRealTime() {
  const context = React.useContext(RealTimeContext)
  if (!context) {
    throw new Error('useRealTime must be used within a RealTimeProvider')
  }
  return context
}

// Hook for subscribing to specific repository updates
export function useRepositoryUpdates(repositoryId: string): ComplianceUpdate | undefined {
  const { complianceUpdates } = useRealTime()
  return complianceUpdates.get(repositoryId)
}

// Live indicator component (pulsing dot)
export function LiveIndicator({ className }: { className?: string }) {
  return (
    <span className={clsx('relative flex h-2 w-2', className)}>
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
    </span>
  )
}

// Real-time notification bell
interface NotificationBellProps {
  onClick?: () => void
  className?: string
}

export function NotificationBell({ onClick, className }: NotificationBellProps) {
  const { unreadCount, status } = useRealTime()

  return (
    <button
      onClick={onClick}
      className={clsx(
        'relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
        className
      )}
    >
      <svg
        className="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      
      {/* Unread badge */}
      {unreadCount > 0 && (
        <span className="absolute top-0.5 right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
      
      {/* Connection indicator */}
      {status === 'connected' && (
        <span className="absolute bottom-1 right-1">
          <LiveIndicator />
        </span>
      )}
    </button>
  )
}
