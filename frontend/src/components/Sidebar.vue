<script setup lang="ts">
import { inject, ref, watch } from "vue";
import type {
  ConnectionInfo,
  ScanProgress,
  ExtensionInfo,
} from "@/types";

const emit = defineEmits<{
  (e: "startScan"): void;
  (e: "stopScan"): void;
}>();

const conn = inject<any>("connections")!;
const scan = inject<any>("scan")!;
const ws = inject<any>("webSocket")!;
const ext = inject<any>("extensions")!;

const adding = ref(false);
const newConn = ref<Partial<ConnectionInfo>>({
  id: "",
  name: "",
  host: "localhost",
  port: 5236,
  user: "",
  password: "",
  schema: "",
});

function startAdd() {
  adding.value = true;
  newConn.value = { id: "", name: "", host: "localhost", port: 5236, user: "", password: "", schema: "" };
}

async function saveNew() {
  if (!newConn.value.id || !newConn.value.name) return;
  await conn.save({
    id: newConn.value.id,
    name: newConn.value.name,
    host: newConn.value.host || "localhost",
    port: newConn.value.port || 5236,
    user: newConn.value.user || "",
    password: newConn.value.password || "",
    schema: newConn.value.schema || "",
    last_scan: null,
  } as ConnectionInfo);
  adding.value = false;
  conn.select(newConn.value.id);
}

const progressPct = ref(0);
watch(
  () => ws.progress,
  (p: ScanProgress) => {
    if (p.tablesTotal > 0) {
      progressPct.value = Math.round((p.tablesDone / p.tablesTotal) * 100);
    }
  }
);

const extensions = inject<{ extensions: { value: ExtensionInfo[] }; load: () => void }>("extensions")!;
</script>

<template>
  <div class="sidebar-inner">
    <!-- 连接列表 -->
    <div class="section">
      <div class="section-title">数据库连接</div>
      <div
        v-for="c in conn.connections.value"
        :key="c.id"
        class="conn-item"
        :class="{ active: conn.selectedId.value === c.id }"
        @click="conn.select(c.id)"
      >
        <span
          class="conn-status"
          :style="{ background: c.last_scan ? '#52c41a' : '#bfbfbf' }"
        ></span>
        <span class="conn-name">{{ c.name }}</span>
      </div>
      <div v-if="adding" class="add-form">
        <input
          v-model="newConn.id"
          placeholder="ID (英文标识)"
          class="conn-input"
        />
        <input
          v-model="newConn.name"
          placeholder="名称"
          class="conn-input"
        />
        <input
          v-model="newConn.host"
          placeholder="主机"
          class="conn-input"
        />
        <input
          v-model="newConn.port"
          type="number"
          placeholder="端口"
          class="conn-input"
        />
        <input
          v-model="newConn.user"
          placeholder="用户"
          class="conn-input"
        />
        <input
          v-model="newConn.password"
          type="password"
          placeholder="密码"
          class="conn-input"
        />
        <input
          v-model="newConn.schema"
          placeholder="Schema"
          class="conn-input"
        />
        <div class="add-actions">
          <a-button size="small" @click="saveNew" type="primary">保存</a-button>
          <a-button size="small" @click="adding = false">取消</a-button>
        </div>
      </div>
      <div v-else class="add-btn" @click="startAdd">+ 添加连接</div>
    </div>

    <!-- 扫描控制 -->
    <div class="section">
      <div class="section-title">扫描</div>
      <div v-if="!scan.scanning.value">
        <a-button
          type="primary"
          block
          :disabled="!conn.selectedId.value"
          @click="emit('startScan')"
        >
          启动扫描
        </a-button>
      </div>
      <div v-else>
        <a-button type="primary" danger block @click="emit('stopScan')">
          停止扫描
        </a-button>
      </div>
      <!-- 进度条 -->
      <div v-if="scan.scanning.value && progressPct > 0" class="progress-wrap">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressPct + '%' }"
          ></div>
        </div>
        <div class="progress-text">
          {{ progressPct }}%
          <template v-if="ws.progress.currentTable">
            · {{ ws.progress.currentTable }}
          </template>
        </div>
        <div class="progress-candidates" v-if="ws.progress.candidatesFound">
          已发现 {{ ws.progress.candidatesFound }} 条候选关联
        </div>
      </div>
    </div>

    <!-- 扩展菜单 -->
    <div class="section" style="margin-top: auto">
      <div class="section-title">扩展</div>
      <div
        v-for="ex in extensions.extensions.value"
        :key="ex.id"
        class="ext-item"
      >
        {{ ex.name }}
      </div>
      <div
        v-if="extensions.extensions.value.length === 0"
        class="ext-empty"
      >
        暂无扩展
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.conn-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 2px;
}

.conn-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.conn-item.active {
  background: #e6f7ff;
  color: #1890ff;
}

.conn-status {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.conn-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.add-btn {
  padding: 6px 10px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  cursor: pointer;
  margin-top: 4px;
}

.add-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.conn-input {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  outline: none;
}

.conn-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.add-actions {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.progress-wrap {
  margin-top: 10px;
}

.progress-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s ease;
  border-radius: 2px;
}

.progress-text {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

.progress-candidates {
  font-size: 11px;
  color: #1890ff;
  margin-top: 2px;
}

.ext-item {
  padding: 6px 10px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
  cursor: pointer;
  border-radius: 4px;
}

.ext-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.ext-empty {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.25);
  padding: 4px 10px;
}
</style>
