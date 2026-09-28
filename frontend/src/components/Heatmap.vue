<script setup lang="ts">
import { computed, ref } from "vue"
import type { ContributionDay } from "../types/protocol"

const props = defineProps<{
  days: ContributionDay[]
}>()

const CELL = 11
const GAP = 3
const WEEKS = 53

const tipText = ref("")
const tipVisible = ref(false)
const tipX = ref(0)
const tipY = ref(0)

const grid = computed(() => {
  const columns: Array<Array<ContributionDay | null>> = []
  if (!props.days.length) {
    return columns
  }
  const sorted = props.days.slice().sort((a, b) => a.date.localeCompare(b.date))
  const first = new Date(`${sorted[0].date}T00:00:00Z`)
  const lead = first.getUTCDay()
  let column: Array<ContributionDay | null> = new Array(lead).fill(null)
  for (const day of sorted) {
    column.push(day)
    if (column.length === 7) {
      columns.push(column)
      column = []
    }
    if (columns.length >= WEEKS) {
      break
    }
  }
  if (column.length && columns.length < WEEKS) {
    while (column.length < 7) {
      column.push(null)
    }
    columns.push(column)
  }
  return columns
})

const width = computed(() => grid.value.length * (CELL + GAP))
const height = 7 * (CELL + GAP)

const total = computed(
  () => props.days.reduce((sum, day) => sum + (day.count || 0), 0),
)

function levelClass(day: ContributionDay | null): string {
  if (!day) {
    return "is-empty"
  }
  return `is-level-${Math.min(4, Math.max(0, day.level ?? 0))}`
}

function tooltip(day: ContributionDay | null): string {
  if (!day) {
    return ""
  }
  return `${day.date}：${day.count} 次贡献`
}

function onMove(event: MouseEvent, day: ContributionDay | null): void {
  if (!day) {
    tipVisible.value = false
    return
  }
  tipText.value = tooltip(day)
  tipX.value = event.clientX
  tipY.value = event.clientY
  tipVisible.value = true
}

function onLeave(): void {
  tipVisible.value = false
}
</script>

<template>
  <section class="card">
    <h2 class="card-title">
      贡献热力图
      <span class="chip">近一年 {{ total }} 次</span>
    </h2>
    <div v-if="grid.length" class="heatmap-wrap" @mouseleave="onLeave">
      <svg
        class="heatmap"
        :width="width"
        :height="height"
        :viewBox="`0 0 ${width} ${height}`"
        role="img"
        aria-label="GitHub 贡献热力图"
      >
        <template v-for="(column, weekIndex) in grid" :key="weekIndex">
          <rect
            v-for="(day, dayIndex) in column"
            :key="`${weekIndex}-${dayIndex}`"
            :x="weekIndex * (CELL + GAP)"
            :y="dayIndex * (CELL + GAP)"
            :width="CELL"
            :height="CELL"
            rx="2"
            :class="levelClass(day)"
            @mousemove="onMove($event, day)"
          >
            <title>{{ tooltip(day) }}</title>
          </rect>
        </template>
      </svg>
      <div
        v-if="tipVisible"
        class="heat-tip"
        :style="{ left: `${tipX}px`, top: `${tipY}px` }"
      >
        {{ tipText }}
      </div>
    </div>
    <p v-else class="muted empty">暂无贡献数据</p>
  </section>
</template>

<style scoped>
.heatmap-wrap {
  overflow-x: auto;
  padding-bottom: 4px;
  position: relative;
}

.heatmap {
  display: block;
  max-width: 100%;
  height: auto;
}

.heatmap rect.is-empty {
  fill: transparent;
}

.heatmap rect.is-level-0 {
  fill: var(--heat-0);
}

.heatmap rect.is-level-1 {
  fill: var(--heat-1);
}

.heatmap rect.is-level-2 {
  fill: var(--heat-2);
}

.heatmap rect.is-level-3 {
  fill: var(--heat-3);
}

.heatmap rect.is-level-4 {
  fill: var(--heat-4);
}

.empty {
  margin: 0;
}

.heat-tip {
  position: fixed;
  z-index: 50;
  pointer-events: none;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 0.78rem;
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-container-high);
  border: 1px solid var(--md-sys-color-outline-variant);
  box-shadow: var(--md-sys-elevation-2);
  transform: translate(-50%, -120%);
  white-space: nowrap;
}
</style>
