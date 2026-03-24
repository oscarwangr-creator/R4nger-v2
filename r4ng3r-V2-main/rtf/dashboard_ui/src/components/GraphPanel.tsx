import { useMemo, useState } from 'react';

type GraphNode = {
  id: string;
  label?: string;
  value?: string;
  entity_type: string;
  source_module?: string;
  properties?: Record<string, unknown>;
};

type GraphEdge = {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship: string;
};

type GraphPanelProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodeId?: string | null;
  onNodeSelect?: (node: GraphNode) => void;
  onPivot?: (node: GraphNode) => void;
};

const colorMap: Record<string, string> = {
  Person: '#ef4444',
  Username: '#f97316',
  Email: '#a855f7',
  Phone: '#14b8a6',
  Domain: '#3b82f6',
  Organization: '#f59e0b',
  Account: '#ec4899',
  IP: '#22c55e',
};

export function GraphPanel({ nodes, edges, highlightedNodeId, onNodeSelect, onPivot }: GraphPanelProps) {
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const positionedNodes = useMemo(() => {
    const width = 920;
    const height = 460;
    const cx = width / 2;
    const cy = height / 2;
    return nodes.map((node, index) => {
      const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2;
      const ring = 120 + (index % 4) * 42;
      return {
        ...node,
        x: cx + Math.cos(angle) * ring,
        y: cy + Math.sin(angle) * ring,
      };
    });
  }, [nodes]);

  const nodeMap = useMemo(() => new Map(positionedNodes.map((node) => [node.id, node])), [positionedNodes]);
  const detail = selected ?? positionedNodes.find((node) => node.id === highlightedNodeId) ?? null;

  return (
    <div className="graph-shell">
      <div className="graph-stage">
        <svg className="graph-surface" viewBox="0 0 920 460" role="img" aria-label="RTF intelligence graph">
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" fill="#f87171" />
            </marker>
          </defs>
          {edges.map((edge) => {
            const source = nodeMap.get(edge.source_node_id);
            const target = nodeMap.get(edge.target_node_id);
            if (!source || !target) return null;
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            return (
              <g key={edge.id}>
                <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#334155" strokeWidth="1.5" markerEnd="url(#arrow)" />
                <text x={midX} y={midY - 6} textAnchor="middle" fill="#94a3b8" fontSize="10">{edge.relationship}</text>
              </g>
            );
          })}
          {positionedNodes.map((node) => {
            const active = detail?.id === node.id || highlightedNodeId === node.id;
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => {
                  setSelected(node);
                  onNodeSelect?.(node);
                }}
                onDoubleClick={() => onPivot?.(node)}
                style={{ cursor: 'pointer' }}
              >
                <circle r={active ? 20 : 16} fill={colorMap[node.entity_type] ?? '#64748b'} stroke={active ? '#f8fafc' : '#0f172a'} strokeWidth="2" />
                <text y="34" textAnchor="middle" fill="#e2e8f0" fontSize="11">{node.label || node.value || node.id}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="graph-detail panel-subtle">
        <div>
          <span className="eyebrow">Selected entity</span>
          <h3>{detail ? detail.label || detail.value || detail.id : 'No entity selected'}</h3>
          <p>{detail ? `${detail.entity_type} · ${detail.source_module ?? 'manual seed'}` : 'Click any node to inspect context, then double-click to pivot.'}</p>
        </div>
        {detail && (
          <div className="detail-grid">
            <div>
              <span className="detail-label">Node ID</span>
              <code>{detail.id}</code>
            </div>
            <div>
              <span className="detail-label">Type</span>
              <code>{detail.entity_type}</code>
            </div>
            <div className="detail-actions">
              <button type="button" onClick={() => onPivot?.(detail)}>
                Pivot Investigation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
