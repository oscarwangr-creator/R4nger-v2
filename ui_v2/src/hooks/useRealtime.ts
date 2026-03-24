import { useEffect, useState } from 'react'

export function useRealtime(url: string): string {
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    const ws = new WebSocket(url)
    ws.onopen = () => setStatus('connected')
    ws.onerror = () => setStatus('error')
    ws.onclose = () => setStatus('closed')
    return () => ws.close()
  }, [url])

  return status
}
