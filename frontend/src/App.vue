<script setup lang="ts">
import {
  ref,
  provide,
  onMounted,
  watch,
  computed,
} from "vue";
import type { AgentStatus as AgentStatusType } from "@/types";
import Sidebar from "@/components/Sidebar.vue";
import RelationList from "@/components/RelationList.vue";
import RelationGraph from "@/components/RelationGraph.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import AgentStatus from "@/components/AgentStatus.vue";
import ScanConfig from "@/components/ScanConfig.vue";
import {
  useConnections,
  useRelations,
  useWebSocket,
  useScan,
  useScanConfig,
  useExtensions,
} from "@/composables";

const conn = useConnections();
const rel = useRelations();
const ws = useWebSocket();
const scan = useScan();
const scanConfig = useScanConfig();
const ext = useExtensions();

const showConfig = ref(false);
const selectedTable = ref<string | null>(null);
const selectedFromTable = ref<string | null>(null);
const selectedToTable = ref<string | null>(null);

const wsPort = computed(() => scanConfig.config.value.ws_port);

// 同时提供给子组件
provide("connections", conn);
provide("relations", rel);
provide("webSocket", ws);
provide("scan", scan);
provide("scanConfig", scanConfig.config);
provide("scanConfigSave", scanConfig.save);
provide("extensions", ext);
provide("selectedTable", selectedTable);
provide("selectedFromTable", selectedFromTable);
provide("selectedToTable", selectedToTable);
provide("showConfig", showConfig);

onMounted(async () => {
  await conn.load();
  await scanConfig.load();
  await ext.load();
  // 默认选中第一个连接
  if (conn.connections.value.length > 0) {
    conn.select(conn.connections.value[0].id);
  }
});

// 选择连接后加载数据
watch(conn.selectedId, async (id) => {
  if (id) {
    await rel.load(id);
  } else {
    rel.clear();
  }
});

// WS 状态联动 Agent 状态
watch(
  () => ws.status.value,
  (s) => {
    if (s === "connected") {
      scan.agentStatus.value = "scanning";
    } else if (s === "disconnected" && scan.agentStatus.value === "scanning") {
      // 可能扫描完了
    }
  }
);

watch(
  () => ws.lastMessage.value,
  (msg) => {
    if (!msg) return;
    if (msg.type === "phase" && msg.phase === "analyzing") {
      scan.agentStatus.value = "analyzing";
    }
    if (msg.type === "done") {
      scan.agentStatus.value = "done";
      scan.scanning.value = false;
      ws.disconnect();
      if (conn.selectedId.value) {
        rel.load(conn.selectedId.value);
        // 更新最后扫描时间
        const c = conn.connections.value.find(
          (x) => x.id === conn.selectedId.value
        );
        if (c) c.last_scan = new Date().toISOString().slice(0, 19);
      }
      setTimeout(() => {
        scan.agentStatus.value = "offline";
      }, 5000);
    }
    if (msg.type === "error") {
      scan.agentStatus.value = "error";
      scan.error.value = msg.message || "未知错误";
      scan.scanning.value = false;
      ws.disconnect();
    }
  }
);

function handleStartScan() {
  if (!conn.selectedId.value) return;
  scan.startScan(conn.selectedId.value, undefined, wsPort.value);
  // 等 agent 启动后连接 WS
  setTimeout(() => {
    ws.connect(wsPort.value);
  }, 1500);
}

function handleStopScan() {
  scan.stopScan();
  ws.disconnect();
}

function handleSelectTable(name: string) {
  selectedTable.value = name;
}

function handleSelectRelation(fromTable: string, toTable: string) {
  selectedFromTable.value = fromTable;
  selectedToTable.value = toTable;
  selectedTable.value = fromTable;
}
</script>

<template>
  <div class="app-shell">
    <!-- 顶部栏 -->
    <header class="app-header">
      <div class="header-left">
        <span class="logo">TableScope</span>
        <span class="logo-sub">表关联浏览器</span>
      </div>
      <div class="header-right">
        <AgentStatus
          :status="scan.agentStatus.value"
          :error="scan.error.value"
        />
        <a-button
          type="text"
          size="small"
          @click="showConfig = !showConfig"
        >
          <template #icon>
            <span style="font-size: 16px">&#9881;</span>
          </template>
          设置
        </a-button>
      </div>
    </header>

    <div class="app-body">
      <!-- 左栏 -->
      <aside class="sidebar">
        <Sidebar
          @start-scan="handleStartScan"
          @stop-scan="handleStopScan"
        />
      </aside>

      <!-- 主区域 -->
      <main class="main-area">
        <!-- 设置面板 -->
        <ScanConfig v-if="showConfig" @close="showConfig = false" />

        <!-- 统计卡片 -->
        <div v-if="!showConfig" class="stats-row">
          <div class="stat-card">
            <div class="stat-value">{{ rel.schema.value?.tables?.length || 0 }}</div>
            <div class="stat-label">张表</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ rel.relations.value.length }}</div>
            <div class="stat-label">条关联</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">
              {{ rel.relations.value.filter(r => r.confidence === 'high').length }}
            </div>
            <div class="stat-label">高置信</div>
          </div>
        </div>

        <!-- 关联列表 + 图谱 -->
        <div v-if="!showConfig" class="content-row">
          <div class="list-panel">
            <RelationList
              @select-table="handleSelectTable"
              @select-relation="handleSelectRelation"
            />
          </div>
          <div class="graph-panel">
            <RelationGraph
              @select-table="handleSelectTable"
              @select-relation="handleSelectRelation"
            />
            <DetailPanel :table-name="selectedTable || undefined" />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
/* Global reset */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --color-bg: #f5f5f5;
  --color-surface: #ffffff;
  --color-border: #f0f0f0;
  --color-text: rgba(0, 0, 0, 0.85);
  --color-text-secondary: rgba(0, 0, 0, 0.45);
  --color-primary: #1890ff;
  --sidebar-width: 240px;
  --header-height: 48px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  overflow: hidden;
}

.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  height: var(--header-height);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.logo {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 0.5px;
}

.logo-sub {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.main-area {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px 20px;
  text-align: center;
  min-width: 100px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.content-row {
  display: flex;
  gap: 16px;
  height: calc(100vh - var(--header-height) - 120px);
}

.list-panel {
  width: 400px;
  flex-shrink: 0;
  overflow: auto;
}

.graph-panel {
  flex: 1;
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}
</style>
