<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatRelative, formatTs } from "../utils/format"

const store = useDashboard()

const clientLabel = computed(() => {
  const client = store.status.value?.client
  if (!client) {
    return "未知客户端"
  }
  const version = client.version ? ` · v${client.version}` : ""
  return `${client.id} · ${client.platform}${version}`
})

const onlineText = computed(() => (store.isOnline.value ? "在线" : "离线"))

const heartbeatText = computed(() => formatRelative(store.lastHeartbeatTs.value, store.nowMs.value))

const heartbeatExact = computed(() => formatTs(store.lastHeartbeatTs.value))

const systemMetrics = computed(() => {
  const system = store.status.value?.system
  if (!system) {
    return []
  }
  const load = (system.load_avg ?? []).map((v) => v.toFixed(2)).join(" / ") || "—"
  return [
    { key: "cpu", label: "CPU", value: `${system.cpu_percent.toFixed(1)}%`, ratio: system.cpu_percent / 100 },
    { key: "mem", label: "内存", value: `${system.memory_percent.toFixed(1)}%`, ratio: system.memory_percent / 100 },
    { key: "load", label: "负载 1/5/15", value: load, ratio: null },
  ]
})

const streamLabel = computed(
  () =>
    ({
      sse: "SSE 实时",
      poll: "15s 轮询",
      idle: "未连接",
      connecting: "连接中",
    })[store.streamMode.value],
)
</script>

<template>
  <section class="card live-status">
    <h2 class="card-title">
      实时状态
      <span class="chip stream-chip">{{ streamLabel }}</span>
    </h2>
    <div class="live-row">
      <span class="light" :class="store.isOnline.value ? 'is-online' : 'is-offline'" aria-hidden="true"></span>
      <div class="live-main">
        <div class="live-state">
          <strong>{{ onlineText }}</strong>
          <span class="muted">{{ heartbeatText }}</span>
        </div>
        <div class="muted live-client">{{ clientLabel }}</div>
        <div class="muted live-ts">最近心跳 {{ heartbeatExact }}</div>
      </div>
    </div>
    <div v-if="systemMetrics.length" class="metrics">
      <div v-for="metric in systemMetrics" :key="metric.key" class="metric">
        <div class="metric-head">
          <span>{{ metric.label }}</span>
          <span class="metric-value">{{ metric.value }}</span>
        </div>
        <div v-if="metric.ratio !== null" class="metric-track">
          <div class="metric-fill" :style="{ width: `${Math.min(100, Math.max(0, metric.ratio * 100))}%` }"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.live-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.light {
  width: 14px;
  height: 14px;
  margin-top: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.is-online {
  background: var(--md-sys-color-success);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--md-sys-color-success) 25%, transparent);
}

.is-offline {
  background: var(--md-sys-color-outline);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--md-sys-color-outline) 20%, transparent);
}

.live-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.live-state {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font: var(--md-sys-typescale-title);
}

.live-client,
.live-ts {
  font-size: 0.85rem;
}

.stream-chip {
  margin-left: auto;
}

.metrics {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.metric-head {
  display: flex;
  justify-content: space-between;
  font: var(--md-sys-typescale-label);
  margin-bottom: 6px;
}

.metric-value {
  color: var(--md-sys-color-on-surface-variant);
}

.metric-track {
  height: 8px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--md-sys-color-primary);
  transition: width 0.4s ease;
}
</style>
