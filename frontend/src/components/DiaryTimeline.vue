<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatTs, monthLabel } from "../utils/format"
import type { Diary } from "../types/protocol"

const store = useDashboard()
const activeMonth = ref<string | null>(null)
const loadingMonth = ref<string | null>(null)
const expandedId = ref<number | null>(null)
const closeBtn = ref<HTMLButtonElement | null>(null)

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

const activeItems = computed(() => {
  const group = groups.value.find((item) => item.label === activeMonth.value)
  return group?.items ?? []
})

const expanded = computed(() => {
  return activeItems.value.find((item) => item.id === expandedId.value) ?? null
})

function preview(item: Diary): string {
  const text = item.content.replace(/\s+/g, " ").trim()
  return text.length > 64 ? `${text.slice(0, 64)}…` : text
}

async function toggleMonth(label: string): Promise<void> {
  if (activeMonth.value === label) {
    activeMonth.value = null
    expandedId.value = null
    return
  }
  activeMonth.value = label
  expandedId.value = null
  loadingMonth.value = label
  await nextTick()
  window.setTimeout(() => {
    if (loadingMonth.value === label) {
      loadingMonth.value = null
    }
  }, 220)
}

function openEntry(item: Diary): void {
  expandedId.value = item.id
}

function closeEntry(): void {
  expandedId.value = null
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    closeEntry()
  }
}

watch(expanded, async (value) => {
  document.body.style.overflow = value ? "hidden" : ""
  if (value) {
    await nextTick()
    closeBtn.value?.focus()
    window.addEventListener("keydown", onKeydown)
    return
  }
  window.removeEventListener("keydown", onKeydown)
})
</script>

<template>
  <section class="card">
    <h2 class="card-title">日记</h2>
    <div v-if="groups.length" class="months">
      <article v-for="group in groups" :key="group.label" class="month">
        <button
          type="button"
          class="month-head"
          :class="{ 'is-open': activeMonth === group.label }"
          @click="toggleMonth(group.label)"
        >
          <span class="month-title">{{ group.label }}</span>
          <span class="muted count">{{ group.items.length }} 篇</span>
          <span class="caret" aria-hidden="true"></span>
        </button>
        <div v-if="activeMonth === group.label" class="month-body">
          <div v-if="loadingMonth === group.label" class="loading">
            <span class="spinner" aria-hidden="true"></span>
            <span class="muted">加载中…</span>
          </div>
          <TransitionGroup v-else name="list" tag="div" class="entries">
            <article v-for="item in activeItems" :key="item.id" class="entry">
              <div class="entry-head">
                <strong>{{ item.title }}</strong>
                <span class="muted">{{ formatTs(item.created_ts) }}</span>
              </div>
              <p class="clamped">{{ preview(item) }}</p>
              <div class="entry-foot">
                <div class="tags">
                  <span v-if="item.mood" class="chip">{{ item.mood }}</span>
                  <span v-for="tag in item.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
                </div>
                <button type="button" class="btn btn-ghost more" @click="openEntry(item)">
                  阅读全文
                </button>
              </div>
            </article>
          </TransitionGroup>
        </div>
      </article>
    </div>
    <p v-else class="muted empty">暂无日记</p>
  </section>

  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="expanded"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-label="日记全文"
        @click.self="closeEntry"
      >
        <article class="dialog">
          <header class="dialog-head">
            <div>
              <h3>{{ expanded.title }}</h3>
              <p class="muted">{{ formatTs(expanded.created_ts) }}</p>
            </div>
            <button ref="closeBtn" type="button" class="btn btn-ghost" @click="closeEntry">
              关闭
            </button>
          </header>
          <div class="tags">
            <span v-if="expanded.mood" class="chip">{{ expanded.mood }}</span>
            <span v-for="tag in expanded.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
          </div>
          <div class="dialog-body">{{ expanded.content }}</div>
        </article>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.months {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.month {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
  background: color-mix(in srgb, var(--md-sys-color-surface) 92%, transparent);
}

.month-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.month-head.is-open {
  background: color-mix(in srgb, var(--md-sys-color-primary) 12%, transparent);
}

.month-title {
  font: var(--md-sys-typescale-title);
  font-size: 1rem;
}

.count {
  margin-left: auto;
  font-size: 0.82rem;
}

.caret {
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(45deg);
  opacity: 0.7;
  transition: transform 0.15s ease;
}

.month-head.is-open .caret {
  transform: rotate(225deg);
}

.month-body {
  padding: 0 12px 12px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 8px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.entries {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.entry {
  padding: 12px 14px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container);
}

.entry-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.clamped {
  margin: 8px 0;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.entry-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.more {
  flex-shrink: 0;
}

.empty {
  margin: 0;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 110;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: color-mix(in srgb, var(--md-sys-color-surface) 42%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.dialog {
  width: min(720px, 100%);
  max-height: 85vh;
  overflow: auto;
  padding: 22px;
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container-high);
  box-shadow: var(--md-sys-elevation-3);
}

.dialog-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.dialog-head h3 {
  margin: 0 0 4px;
}

.dialog-body {
  margin-top: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
}
</style>
