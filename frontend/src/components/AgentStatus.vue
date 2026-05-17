<script setup lang="ts">
import type { AgentStatus as AgentStatusType } from "@/types";

const props = defineProps<{
  status: AgentStatusType;
  error?: string;
}>();

const statusConfig: Record<
  AgentStatusType,
  { color: string; label: string; animated: boolean }
> = {
  offline: { color: "#bfbfbf", label: "Agent 离线", animated: false },
  starting: { color: "#faad14", label: "启动中...", animated: true },
  scanning: { color: "#1890ff", label: "扫描中", animated: true },
  analyzing: { color: "#1890ff", label: "分析中", animated: true },
  done: { color: "#52c41a", label: "完成", animated: false },
  error: { color: "#ff4d4f", label: props.error || "错误", animated: false },
};
</script>

<template>
  <div class="agent-status" :title="statusConfig[status].label">
    <span
      class="status-dot"
      :class="{ animated: statusConfig[status].animated }"
      :style="{ background: statusConfig[status].color }"
    ></span>
    <span class="status-text">{{ statusConfig[status].label }}</span>
  </div>
</template>

<style scoped>
.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  transition: background 0.3s;
}

.status-dot.animated {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
