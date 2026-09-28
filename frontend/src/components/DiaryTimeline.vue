<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatTs, monthLabel } from "../utils/format"
import type { Diary } from "../types/protocol"

const store = useDashboard()

const groups = computed(() => {
  const map = new Map<string, Diary[]>()
  for (const diary of store.diaries.value) {
    const key = monthLabel(diary.created_ts)
    const list = map.get(key) ?? []
    list.push(diary)
    map.set(key, list)
  }
  return Array.from(map.entries()).map(([label, items]) => ({
    label,
    items: items.slice().sort((a, b) => b.created_ts - a.created_ts),
  }))
})
</script>

<template>
  <section class="card">
    <h2 class="card-title">日记</h2>
    <div v-if="groups.length" class="timeline">
      <div v-for="group in groups" :key="group.label" class="group">
        <h3 class="group-label">{{ group.label }}</h3>
        <TransitionGroup name="list" tag="div" class="group-items">
          <article v-for="item in group.items" :key="item.id" class="entry">
            <div class="entry-head">
              <strong>{{ item.title }}</strong>
              <span class="muted">{{ formatTs(item.created_ts) }}</span>
            </div>
            <p class="content">{{ item.content }}</p>
            <div class="tags">
              <span v-if="item.mood" class="chip">{{ item.mood }}</span>
              <span v-for="tag in item.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
            </div>
          </article>
        </TransitionGroup>
      </div>
    </div>
    <p v-else class="muted empty">暂无日记</p>
  </section>
</template>

<style scoped>
.timeline {
  position: relative;
  padding-left: 18px;
}

.timeline::before {
  content: "";
  position: absolute;
  left: 5px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  border-radius: 2px;
  background: var(--md-sys-color-outline-variant);
}

.group {
  position: relative;
}

.group-label {
  position: sticky;
  top: 0;
  z-index: 1;
  margin: 0 0 10px;
  padding: 6px 10px;
  width: fit-content;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  font: var(--md-sys-typescale-label);
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
}

.entry {
  position: relative;
  padding: 14px 16px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
}

.entry::before {
  content: "";
  position: absolute;
  left: -18px;
  top: 20px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  box-shadow: 0 0 0 3px var(--md-sys-color-surface-container);
}

.entry-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 6px;
  font: var(--md-sys-typescale-label);
}

.content {
  margin: 0 0 10px;
  white-space: pre-wrap;
  word-break: break-word;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.list-enter-active,
.list-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.empty {
  margin: 0;
}

@media (max-width: 560px) {
  .entry-head {
    flex-direction: column;
    gap: 2px;
  }
}
</style>
