<script setup lang="ts">
import { inject, computed } from "vue";
import type { TableSchema, RelationInfo } from "@/types";

const props = defineProps<{
  tableName?: string;
}>();

const rel = inject<any>("relations")!;
const schema = computed(() => rel.schema.value as TableSchema | null);

const tableInfo = computed(() => {
  if (!props.tableName || !schema.value) return null;
  return schema.value.tables.find((t) => t.name === props.tableName) || null;
});

const relatedRelations = computed(() => {
  if (!props.tableName) return [];
  const list = rel.relations.value as RelationInfo[];
  return list.filter(
    (r) => r.from_table === props.tableName || r.to_table === props.tableName
  );
});

function showComment(comment: string | null) {
  if (comment) return comment;
  return "—";
}

function confidenceLabel(c: string) {
  if (c === "high") return "高";
  if (c === "medium") return "中";
  return "低";
}

function confidenceColor(c: string) {
  if (c === "high") return "#52c41a";
  if (c === "medium") return "#faad14";
  return "#ff4d4f";
}
</script>

<template>
  <div v-if="tableInfo" class="detail-panel">
    <div class="panel-header">
      <h3>{{ tableInfo.name }}</h3>
      <span class="row-count">{{ tableInfo.row_count.toLocaleString() }} 行</span>
    </div>

    <div class="panel-section">
      <div class="section-label">关联 ({{ relatedRelations.length }})</div>
      <div
        v-for="r in relatedRelations"
        :key="r.to_table + r.to_column"
        class="rel-item"
      >
        <span class="rel-dir">
          {{ r.from_table === tableInfo.name ? "→" : "←" }}
        </span>
        <span class="rel-name">
          {{ r.from_table === tableInfo.name ? r.to_table : r.from_table }}
        </span>
        <span class="rel-pct" :style="{ color: confidenceColor(r.confidence) }">
          {{ Math.round(r.overlap_rate * 100) }}% {{ confidenceLabel(r.confidence) }}
        </span>
      </div>
    </div>

    <div class="panel-section">
      <div class="section-label">字段 ({{ tableInfo.columns.length }})</div>
      <div
        v-for="col in tableInfo.columns"
        :key="col.name"
        class="col-item"
      >
        <span class="col-name">{{ col.name }}</span>
        <span class="col-type">{{ col.type }}</span>
        <span
          class="col-comment"
          :class="{ noComment: !col.comment }"
        >
          {{ showComment(col.comment) }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-panel {
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: 8px;
  width: 280px;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10;
}

.panel-header {
  padding: 12px 14px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.panel-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1890ff;
}

.row-count {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
}

.panel-section {
  padding: 8px 0;
  border-bottom: 1px solid #fafafa;
  overflow: auto;
}

.panel-section:last-child {
  flex: 1;
  border-bottom: none;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  padding: 4px 14px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.rel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  font-size: 12px;
}

.rel-dir {
  color: rgba(0, 0, 0, 0.3);
  width: 16px;
}

.rel-name {
  flex: 1;
  font-weight: 500;
}

.rel-pct {
  font-size: 11px;
  font-weight: 500;
}

.col-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px;
  font-size: 12px;
}

.col-name {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  min-width: 80px;
}

.col-type {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.35);
  min-width: 60px;
}

.col-comment {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.55);
  flex: 1;
  text-align: right;
}

.col-comment.noComment {
  color: rgba(0, 0, 0, 0.20);
  font-style: italic;
}
</style>
