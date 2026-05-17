<script setup lang="ts">
import {
  inject,
  ref,
  onMounted,
  onUnmounted,
  watch,
  nextTick,
  computed,
} from "vue";
import { Graph } from "@antv/g6";
import type { RelationInfo, TableSchema } from "@/types";

const emit = defineEmits<{
  (e: "selectTable", name: string): void;
  (e: "selectRelation", fromTable: string, toTable: string): void;
}>();

const rel = inject<any>("relations")!;
const selectedTable = inject<any>("selectedTable");
const selectedFromTable = inject<any>("selectedFromTable");
const selectedToTable = inject<any>("selectedToTable");

const container = ref<HTMLDivElement | null>(null);
let graph: Graph | null = null;

const schema = computed(() => rel.schema.value as TableSchema | null);

// 图谱用的图例颜色
const colors = {
  high: "#52c41a",
  medium: "#faad14",
  low: "#ff4d4f",
};

function buildGraphData(relations: RelationInfo[]) {
  const nodeMap: Record<
    string,
    { id: string; degree: number; rowCount: number }
  > = {};
  for (const r of relations) {
    if (!nodeMap[r.from_table]) {
      nodeMap[r.from_table] = { id: r.from_table, degree: 0, rowCount: 0 };
    }
    if (!nodeMap[r.to_table]) {
      nodeMap[r.to_table] = { id: r.to_table, degree: 0, rowCount: 0 };
    }
    nodeMap[r.from_table].degree++;
    nodeMap[r.to_table].degree++;
  }

  // 填入行数
  if (schema.value) {
    for (const t of schema.value.tables) {
      if (nodeMap[t.name]) {
        nodeMap[t.name].rowCount = t.row_count;
      }
    }
  }

  const nodes = Object.values(nodeMap).map((n) => ({
    id: n.id,
    data: {
      label: n.id,
      degree: n.degree,
      rowCount: n.rowCount,
    },
    style: {
      size: Math.max(24, Math.min(60, 20 + n.degree * 6)),
    },
  }));

  const edges = relations.map((r, i) => ({
    id: `e${i}`,
    source: r.from_table,
    target: r.to_table,
    data: {
      fromColumn: r.from_column,
      toColumn: r.to_column,
      overlapRate: r.overlap_rate,
      confidence: r.confidence,
    },
    style: {
      stroke: colors[r.confidence],
      lineWidth: r.confidence === "high" ? 2.5 : r.confidence === "medium" ? 1.5 : 1,
      lineDash: r.confidence === "medium" ? [6, 3] : r.confidence === "low" ? [3, 4] : undefined,
      opacity: 0.7,
    },
  }));

  return { nodes, edges };
}

function initGraph() {
  if (!container.value) return;

  const data = buildGraphData(rel.relations.value as RelationInfo[]);

  graph = new Graph({
    container: container.value,
    data,
    layout: {
      type: "force",
      preventOverlap: true,
      linkDistance: 150,
      nodeStrength: -200,
    },
    behaviors: ["drag-canvas", "zoom-canvas", "drag-element"],
    node: {
      style: {
        fill: "#e6f7ff",
        stroke: "#1890ff",
        lineWidth: 1.5,
        labelText: (d: any) => d.data?.label || d.id,
        labelFontSize: 12,
        labelFill: "rgba(0,0,0,0.85)",
        labelPlacement: "bottom",
        labelOffsetY: 8,
      },
      state: {
        highlighted: {
          fill: "#bae7ff",
          stroke: "#1890ff",
          lineWidth: 3,
          shadowBlur: 8,
          shadowColor: "rgba(24,144,255,0.3)",
        },
      },
    },
    edge: {
      style: {
        endArrow: true,
      },
      state: {
        highlighted: {
          stroke: "#1890ff",
          lineWidth: 3,
          opacity: 1,
          shadowBlur: 4,
          shadowColor: "rgba(24,144,255,0.3)",
        },
        dimmed: {
          opacity: 0.08,
        },
      },
    },
  });

  // 悬停节点
  graph.on("node:pointerenter", (evt: any) => {
    const id = evt.target?.id;
    if (id) emit("selectTable", id);
  });

  // 悬停边
  graph.on("edge:pointerenter", (evt: any) => {
    const edge = evt.target;
    if (edge) {
      const d = graph?.getEdgeData(edge.id);
      if (d) {
        emit("selectRelation", d.source, d.target);
      }
    }
  });

  // 点击节点高亮关联
  graph.on("node:click", (evt: any) => {
    const id = evt.target?.id;
    if (!id || !graph) return;
    emit("selectTable", id);
    highlightNodeEdges(id);
  });

  graph.render();
}

function highlightNodeEdges(nodeId: string) {
  if (!graph) return;
  const nodeData = graph.getNodeData(nodeId);
  if (!nodeData) return;

  // Dim all edges
  const allEdges = graph.getEdgeData();
  for (const e of allEdges) {
    graph.setElementState({ [e.id]: "dimmed" }, "edge");
  }

  // Highlight connected edges
  const connectedEdges = graph.getRelatedEdgesData(nodeId);
  for (const e of connectedEdges) {
    graph.setElementState({ [e.id]: "highlighted" }, "edge");
  }

  graph.setElementState({ [nodeId]: "highlighted" }, "node");
}
</script>

<template>
  <div ref="container" class="graph-container"></div>
</template>

<style scoped>
.graph-container {
  width: 100%;
  height: 100%;
}
</style>
