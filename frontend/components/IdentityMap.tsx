"use client";
import { useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  useNodesState,
  type NodeProps,
  type Node,
} from "@xyflow/react";
import { ShieldCheck, KeyRound } from "lucide-react";
import "@xyflow/react/dist/style.css";
import { Account, Connection, Simulation, label } from "@/lib/types";
type Data = { account: Account; state: string; selected: boolean };
function AccountNode({ data }: NodeProps<Node<Data>>) {
  return (
    <div
      className={`account-node ${data.state} ${data.selected ? "picked" : ""}`}
    >
      <Handle type="target" position={Position.Left} />
      <div
        className={
          "service-icon c-" +
          data.account.category.replaceAll(" ", "-").toLowerCase()
        }
      >
        {data.account.service_name.slice(0, 1)}
      </div>
      <div>
        <strong>{data.account.service_name}</strong>
        <small>{data.account.category}</small>
      </div>
      <span
        className="node-security"
        title={
          data.account.has_passkey
            ? "Passkey enabled"
            : data.account.has_mfa
              ? "MFA enabled"
              : "No MFA"
        }
      >
        {data.account.has_passkey ? (
          <KeyRound size={13} />
        ) : data.account.has_mfa ? (
          <ShieldCheck size={14} />
        ) : (
          <i />
        )}
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { account: AccountNode };
export default function IdentityMap({
  accounts,
  connections,
  selected,
  onSelect,
  simulation,
}: {
  accounts: Account[];
  connections: Connection[];
  selected: string | null;
  onSelect: (id: string) => void;
  simulation: Simulation | null;
}) {
  const initial = useMemo(() => {
    const sorted = [...accounts].sort(
      (a, b) =>
        connections.filter((r) => r.source_account_id === b.id).length -
          connections.filter((r) => r.source_account_id === a.id).length ||
        a.service_name.localeCompare(b.service_name),
    );
    return sorted.map((a, i) => ({
      id: a.id,
      type: "account",
      position:
        i === 0
          ? { x: 20, y: 250 }
          : {
              x: 300 + Math.floor((i - 1) / 5) * 295,
              y: 35 + ((i - 1) % 5) * 112,
            },
      data: { account: a, state: "normal", selected: a.id === selected },
    }));
  }, [accounts, connections, selected]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial);
  useEffect(() => {
    setNodes((previous) =>
      initial.map((n) => ({
        ...n,
        position: previous.find((p) => p.id === n.id)?.position || n.position,
        data: {
          ...n.data,
          state: !simulation
            ? "normal"
            : n.id === simulation.source_account_id
              ? "source"
              : simulation.paths.some((p) => p.target_account_id === n.id)
                ? "affected"
                : "unaffected",
        },
      })),
    );
  }, [initial, simulation, setNodes]);
  const edges = connections.map((r) => {
    const active = simulation?.paths.some((p) =>
      p.relationship_ids.includes(r.id),
    );
    return {
      id: r.id,
      source: r.source_account_id,
      target: r.target_account_id,
      type: "smoothstep",
      label: label(r.relationship_type),
      animated: !!active,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: active ? "#e07b43" : "#9ba9bb",
      },
      style: {
        stroke: active ? "#e07b43" : "#b5c1ce",
        strokeWidth: active ? 2 : 1.3,
        opacity: simulation && !active ? 0.3 : 1,
      },
      labelStyle: { fontSize: 9, fill: "#667487" },
      labelBgStyle: { fill: "#f8fafb" },
      labelBgPadding: [5, 3] as [number, number],
    };
  });
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onNodeClick={(_, n) => onSelect(n.id)}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.25}
      maxZoom={1.6}
      nodesConnectable={false}
      deleteKeyCode={null}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#d8e0e9" gap={20} />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}
