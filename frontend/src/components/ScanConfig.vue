<script setup lang="ts">
import { inject, computed, type Ref } from "vue";
import type { ScanConfig } from "@/types";

const emit = defineEmits<{
  (e: "close"): void;
}>();

const config = inject<Ref<ScanConfig>>("scanConfig")!;
const saveConfig = inject<() => Promise<void>>("scanConfigSave", () => Promise.resolve());

const strategyOptions = [
  { label: "随机采样", value: "sample" },
  { label: "最近数据", value: "recent" },
  { label: "全量", value: "full" },
];

const thresholdPct = computed({
  get: () => Math.round(config.value.overlap_threshold * 100),
  set: (v: number) => { config.value.overlap_threshold = v / 100; },
});

function addRule() {
  config.value.large_table_rules.push({
    min_rows: 1000000,
    strategy: "recent",
    recent_days: 3,
  });
}

function removeRule(index: number) {
  config.value.large_table_rules.splice(index, 1);
}

function addExclude() {
  config.value.exclude_tables.push("");
}

function removeExclude(index: number) {
  config.value.exclude_tables.splice(index, 1);
}

function onWsPort(e: Event) {
  config.value.ws_port = Number((e.target as HTMLInputElement).value);
}

function onSampleRows(e: Event) {
  config.value.sample_rows = Number((e.target as HTMLInputElement).value);
}

function onStrategyChange(v: string) {
  config.value.default_strategy = v as ScanConfig["default_strategy"];
}

function onRuleMinRows(rule: any, e: Event) {
  rule.min_rows = Number((e.target as HTMLInputElement).value);
}

function onRuleStrategy(rule: any, v: string) {
  rule.strategy = v;
}

function onRuleRecentDays(rule: any, e: Event) {
  rule.recent_days = Number((e.target as HTMLInputElement).value);
}

function onRuleSamplePct(rule: any, e: Event) {
  rule.sample_pct = Number((e.target as HTMLInputElement).value);
}

function onExcludeInput(index: number, e: Event) {
  config.value.exclude_tables[index] = (e.target as HTMLInputElement).value;
}

function onThresholdInput(e: Event) {
  thresholdPct.value = Number((e.target as HTMLInputElement).value);
}

async function saveAndClose() {
  await saveConfig();
  emit("close");
}
</script>

<template>
  <div class="config-overlay">
    <div class="config-panel">
      <div class="config-header">
        <h3>扫描设置</h3>
        <a-button type="text" size="small" @click="emit('close')">✕</a-button>
      </div>

      <div class="config-body">
        <div class="cfg-item">
          <label>Agent 启动命令</label>
          <a-input v-model:value="config.agent_command" size="small" />
        </div>

        <div class="cfg-row">
          <div class="cfg-item">
            <label>WS 端口</label>
            <input type="number" class="cfg-input" :value="config.ws_port" @input="onWsPort" min="1024" max="65535" />
          </div>
          <div class="cfg-item">
            <label>默认采样行数</label>
            <input type="number" class="cfg-input" :value="config.sample_rows" @input="onSampleRows" min="100" max="100000" />
          </div>
        </div>

        <div class="cfg-item">
          <label>默认采样策略</label>
          <a-select :value="config.default_strategy" :options="strategyOptions" size="small" @change="onStrategyChange" />
        </div>

        <div class="cfg-item">
          <label>重合度阈值: {{ thresholdPct }}%</label>
          <input type="range" class="cfg-range" :value="thresholdPct" @input="onThresholdInput" min="10" max="90" step="5" />
        </div>

        <div class="cfg-section">
          <label>大表规则</label>
          <div v-for="(rule, i) in config.large_table_rules" :key="i" class="rule-row">
            <input type="number" class="cfg-input" style="width:100px" :value="rule.min_rows" @input="onRuleMinRows(rule, $event)" placeholder="行数阈值" />
            <a-select :value="rule.strategy" :options="strategyOptions" size="small" style="width:110px" @change="onRuleStrategy(rule, $event)" />
            <input v-if="rule.strategy === 'recent'" type="number" class="cfg-input" style="width:70px" :value="rule.recent_days" @input="onRuleRecentDays(rule, $event)" placeholder="天数" />
            <input v-if="rule.strategy === 'sample'" type="number" class="cfg-input" style="width:70px" :value="rule.sample_pct" @input="onRuleSamplePct(rule, $event)" placeholder="%" />
            <a-button type="text" size="small" danger @click="removeRule(i)">删除</a-button>
          </div>
          <a-button size="small" type="dashed" block @click="addRule">+ 添加规则</a-button>
        </div>

        <div class="cfg-section">
          <label>排除表 (支持通配符 *, ?)</label>
          <div v-for="(pat, i) in config.exclude_tables" :key="i" class="exclude-row">
            <input class="cfg-input" style="flex:1" :value="pat" @input="onExcludeInput(i, $event)" placeholder="如 tmp_*" />
            <a-button type="text" size="small" danger @click="removeExclude(i)">✕</a-button>
          </div>
          <a-button size="small" type="dashed" block @click="addExclude">+ 添加排除规则</a-button>
        </div>
      </div>

      <div class="config-footer">
        <a-button @click="emit('close')">取消</a-button>
        <a-button type="primary" @click="saveAndClose">保存</a-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-overlay {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  margin-bottom: 16px;
}

.config-panel {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #f0f0f0;
}

.config-header h3 {
  font-size: 14px;
  font-weight: 600;
}

.config-body {
  padding: 14px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.cfg-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cfg-item label,
.cfg-section label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.65);
}

.cfg-row {
  display: flex;
  gap: 12px;
}

.cfg-row .cfg-item {
  flex: 1;
}

.cfg-input {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  background: #fff;
}

.cfg-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.cfg-range {
  width: 100%;
  accent-color: #1890ff;
}

.rule-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.exclude-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid #f0f0f0;
}
</style>
