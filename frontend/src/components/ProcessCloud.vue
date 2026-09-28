<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()

const MAX_WEIGHT = 8

const chips = computed(() => {
  const processes = store.status.value?.processes ?? []
  const maxCount = processes.reduce((max, item) => Math.max(max, item.count ?? 1), 1)
  return processes
    .slice()
    .sort((a, b) => (b.count ?? 1) - (a.count ?? 1))
    .map((item) => {
      const count = item.count ?? 1
      const weight = Math.min(MAX_WEIGHT, 1 + Math.floor((count / maxCount) * (MAX_WEIGHT - 1)))
      return {
        name: item.name,
        count,
        weight,
      }
    })
})
</script>

<template>
  <section class="card">
    <h2 class="card-title">软件标签云</h2>
    <div v-if="chips.length" class="cloud">
      <span
        v-for="chip in chips"
        :key="chip.name"
        class="chip cloud-chip"
        :style="{ '--w': chip.weight }"
        :title="`${chip.name} ×${chip.count}`"
      >
        {{ chip.name }}
        <em v-if="chip.count > 1">×{{ chip.count }}</em>
      </span>
    </div>
    <p v-else class="muted empty">暂无进程数据</p>
  </section>
</template>

<style scoped>
.cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cloud-chip {
  font-size: calc(12px + var(--w, 1) * 1.6px);
  padding: 8px 14px;
  transition: transform 0.15s ease;
}

.cloud-chip:hover {
  transform: translateY(-1px);
}

.cloud-chip em {
  font-style: normal;
  opacity: 0.65;
  font-size: 0.85em;
  margin-left: 4px;
}

.empty {
  margin: 0;
}
</style>
