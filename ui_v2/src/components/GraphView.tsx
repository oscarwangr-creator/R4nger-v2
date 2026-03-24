import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'

export function GraphView() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const cy = cytoscape({
      container: ref.current,
      elements: [
        { data: { id: 'target', label: 'Target' } },
        { data: { id: 'email', label: 'Email' } },
        { data: { id: 'domain', label: 'Domain' } },
        { data: { source: 'target', target: 'email' } },
        { data: { source: 'target', target: 'domain' } },
      ],
      style: [
        { selector: 'node', style: { label: 'data(label)', 'background-color': '#06b6d4', color: '#e2e8f0' } },
        { selector: 'edge', style: { width: 2, 'line-color': '#334155' } },
      ],
      layout: { name: 'cose' },
    })
    return () => cy.destroy()
  }, [])

  return <div className="h-96 w-full rounded-xl border border-slate-700" ref={ref} />
}
