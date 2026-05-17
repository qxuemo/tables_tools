<script setup lang="ts">
import { inject, computed, ref } from "vue";
import type { RelationInfo, TableSchema } from "@/types";

const emit = defineEmits<{
  (e: "selectTable", name: string): void;
  (e: "selectRelation", fromTable: string, toTable: string): void;
}>();

const rel = inject<any>("relations")!;
const selectedTable = inject<any>("selectedTable");

const search = ref("");
const expanded: Record<string, boolean> = {};

// 按 from_table 分组
const grouped = computed(() => {
  const g: Record<string, RelationInfo[]> = {};
  let list = rel.relations.value as RelationInfo[];

  if (search.value) {
    const q = search.value.toLowerCase();
    list = list.filter(
      (r) =>
        r.from_table.toLowerCase().includes(q) ||
        r.to_table.toLowerCase().includes(q) ||
        r.from_column.toLowerCase().includes(q) ||
        r.to_column.toLowerCase().includes(q)
    );
  }

  for (const r of list) {
    if (!g[r.from_table]) g[r.from_table] = [];
    g[r.from_table].push(r);
  }

  // 按关联数量降序
  const sorted: [string, RelationInfo[]][] = Object.entries(g).sort(
    (a, b) => b[1].length - a[1].length
  );
  return sorted;
});

function toggleExpand(key: string) {
  expanded[key] = !expanded[key];
}

function confidenceColor(c: string) {
  if (c === "high") return "#52c41a";
  if (c === "medium") return "#faad14";
  return "#ff4d4f";
}

function confidenceWidth(v: number) {
  return Math.round(v * 100) + "%";
}

const schema = computed(() => rel.schema.value as TableSchema | null);
const tableMap = computed(() => {
  const m: Record<string, { row_count: number; comment?: string | null }> = {};
  if (schema.value) {
    for (const t of schema.value.tables) {
      m[t.name] = { row_count: t.row_count };
    }
  }
  return m;
});
</script>

<template>
  <div class="relation-list">
    <div class="list-header">
      <a-input
        v-model:value="search"
        placeholder="搜索表名或字段..."
        size="small"
        allow-clear
      />
    </div>
    <div class="list-body">
      <div
        v-for="[table, rels] in grouped"
        :key="table"
        class="group"
      >
        <div
          class="group-header"
          :class="{ selected: selectedTable?.value === table }"
          @click="toggleExpand(table)"
        >
          <span class="group-arrow">
            {{ expanded[table] !== false ? "▾" : "▸" }}
          </span>
          <span class="group-name">{{ table }}</span>
          <span class="group-count">{{ rels.length }} 关联</span>
        </div>
        <div
          v-if="expanded[table] !== false"
          class="group-rows"
        >
          <div
            v-for="r in rels"
            :key="r.to_table + r.to_column"
            class="rel-row"
            @click="emit('selectRelation', r.from_table, r.to_table)"
          >
            <div class="rel-info">
              <span class="rel-to">{{ r.to_table }}</span>
              <span class="rel-cols">
                {{ r.from_column }} &rarr; {{ r.to_column }}
              </span>
            </div>
            <div class="rel-confidence">
              <div class="confidence-bar">
                <div
                  class="confidence-fill"
                  :style="{
                    width: confidenceWidth(r.overlap_rate),
                    background: confidenceColor(r.confidence),
                  }"
                ></div>
              </div>
              <span
                class="confidence-pct"
                :style="{ color: confidenceColor(r.confidence) }"
              >
                {{ Math.round(r.overlap_rate * 100) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
      <div v-if="grouped.length === 0" class="empty-state">
        <p v-if="search">无匹配结果</p>
        <p v-else>暂无关联数据</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.relation-list {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #f0f0f0);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
}

.list-body {
  flex: 1;
  overflow: auto;
  padding: 4px 0;
}

.group {
  border-bottom: 1px solid #fafafa;
}

.group:last-child {
  border-bottom: none;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.group-header:hover {
  background: rgba(0, 0, 0, 0.02);
}

.group-header.selected {
  background: #e6f7ff;
}

.group-arrow {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.3);
  width: 14px;
}

.group-name {
  color: #1890ff;
}

.group-count {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.35);
  margin-left: auto;
}

.group-rows {
  padding: 0 12px 8px 28px;
}

.rel-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  gap: 12px;
}

.rel-row:hover {
  background: rgba(0, 0, 0, 0.03);
}

.rel-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.rel-to {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rel-cols {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.rel-confidence {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.confidence-bar {
  width: 60px;
  height: 3px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
}

.confidence-pct {
  font-size: 11px;
  font-weight: 500;
  width: 32px;
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: rgba(0, 0, 0, 0.25);
  font-size: 13px;
}
</style>
