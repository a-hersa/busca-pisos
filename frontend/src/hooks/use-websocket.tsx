'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '@/types'
import { useAuth } from './use-auth'
import toast from 'react-hot-toast'

interface UseWebSocketReturn {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: any) => void
}

export function useWebSocket(): UseWebSocketReturn {
  const { user } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    if (!user) return

    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001'
    const wsUrl = `${WS_URL}/ws/${user.user_id}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // Skip echo messages
          if (data.startsWith && data.startsWith('Message received:')) {
            return
          }

          setLastMessage(data)
          
          // Show job notifications
          if (data.type === 'job_update') {
            switch (data.status) {
              case 'completed':
                toast.success(`Job completado: ${data.details?.items_scraped || 0} elementos encontrados`)
                break
              case 'failed':
                toast.error(`Job falló: ${data.details?.error || 'Error desconocido'}`)
                break
              case 'running':
                toast.loading(`Job iniciado: ${data.job_id}`, { id: `job-${data.job_id}` })
                break
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [user])

  return {
    isConnected,
    lastMessage,
    sendMessage,
  }
}