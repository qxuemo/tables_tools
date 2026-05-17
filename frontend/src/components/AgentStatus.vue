<script setup lang="ts">
import type { AgentStatus as AgentStatusType } from "@/types";

const props = defineProps<{
  status: AgentStatusType;
  error?: string;
}>();

import { computed } from "vue";

const statusLabel = computed(() => {
  if (props.status === "error") return props.error || "错误";
  const labels: Record<string, string> = {
    offline: "Agent 离线",
    starting: "启动中...",
    scanning: "扫描中",
    analyzing: "分析中",
    done: "完成",
  };
  return labels[props.status] || props.status;
});

const statusColor = computed(() => {
  const colors: Record<string, string> = {
    offline: "#bfbfbf",
    starting: "#faad14",
    scanning: "#1890ff",
    analyzing: "#1890ff",
    done: "#52c41a",
    error: "#ff4d4f",
  };
  return colors[props.status] || "#bfbfbf";
});

const isAnimated = computed(() =>
  ["starting", "scanning", "analyzing"].includes(props.status)
);
</script>

<template>
  <div class="agent-status" :title="statusLabel">
    <span
      class="status-dot"
      :class="{ animated: isAnimated }"
      :style="{ background: statusColor }"
    ></span>
    <span class="status-text">{{ statusLabel }}</span>
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
