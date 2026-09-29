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
const query = ref("")
const activeTag = ref("")
const monthRefs = new Map<string, HTMLElement>()

const allTags = computed(() => {
  const set = new Set<string>()
  for (const item of store.diaries.value) {
    for (const tag of item.tags ?? []) {
      if (tag) {
        set.add(tag)
      }
    }
    if (item.mood) {
      set.add(item.mood)
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
})

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return store.diaries.value.filter((item) => {
    if (activeTag.value) {
      const tags = item.tags ?? []
      const hasTag = tags.includes(activeTag.value) || item.mood === activeTag.value
      if (!hasTag) {
        return false
      }
    }
    if (!q) {
      return true
    }
    const hay = `${item.title}\n${item.content}`.toLowerCase()
    return hay.includes(q)
  })
})

const latest = computed(() => {
  return store.diaries.value
    .slice()
    .sort((a, b) => b.created_ts - a.created_ts)[0] ?? null
})

const groups = computed(() => {
  const map = new Map<string, Diary[]>()
  for (const diary of filtered.value) {
    const key = monthLabel(diary.created_ts)
    const list = map.get(key) ?? []
    list.push(diary)
    map.set(key, list)
  }
  return Array.from(map.entries()).map(([label, items]) => {
    const date = new Date(items[0].created_ts)
    return {
      label,
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      items: items.slice().sort((a, b) => b.created_ts - a.created_ts),
    }
  })
})

const yearGroups = computed(() => {
  const map = new Map<number, typeof groups.value>()
  for (const group of groups.value) {
    const list = map.get(group.year) ?? []
    list.push(group)
    map.set(group.year, list)
  }
  return Array.from(map.entries())
    .sort((a, b) => b[0] - a[0])
    .map(([year, months]) => ({
      year,
      months: months.slice().sort((a, b) => b.month - a.month),
    }))
})

const activeItems = computed(() => {
  const group = groups.value.find((item) => item.label === activeMonth.value)
  return group?.items ?? []
})

const expanded = computed(() => {
  const all = store.diaries.value
  return all.find((item) => item.id === expandedId.value) ?? null
})

const latestPreview = computed(() => {
  if (!latest.value) {
    return ""
  }
  return clampText(latest.value.content, 120)
})

function clampText(text: string, max: number): string {
  const normalized = text.replace(/\s+/g, " ").trim()
  return normalized.length > max ? `${normalized.slice(0, max)}…` : normalized
}

function preview(item: Diary): string {
  return clampText(item.content, 64)
}

function setMonthRef(label: string, el: unknown): void {
  if (el instanceof HTMLElement) {
    monthRefs.set(label, el)
  }
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

function jumpToMonth(label: string): void {
  void toggleMonth(label)
  window.setTimeout(() => {
    monthRefs.get(label)?.scrollIntoView({ behavior: "smooth", block: "start" })
  }, 30)
}

function openEntry(item: Diary): void {
  expandedId.value = item.id
}

function closeEntry(): void {
  expandedId.value = null
}

function clearFilters(): void {
  query.value = ""
  activeTag.value = ""
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

watch([query, activeTag], () => {
  activeMonth.value = null
  expandedId.value = null
})
</script>

<template>
  <div class="diary-page">
    <aside class="rail" aria-label="月份导航">
      <h3 class="rail-title">时间轴</h3>
      <div v-if="yearGroups.length" class="year-list">
        <section v-for="yearGroup in yearGroups" :key="yearGroup.year" class="year-block">
          <div class="year-label">{{ yearGroup.year }}</div>
          <div class="month-grid">
            <button
              v-for="month in yearGroup.months"
              :key="month.label"
              type="button"
              class="month-chip"
              :class="{ 'is-active': activeMonth === month.label }"
              :title="`${month.month} 月 · ${month.items.length} 篇`"
              @click="jumpToMonth(month.label)"
            >
              <span class="month-num">{{ month.month }} 月</span>
              <span class="month-count">{{ month.items.length }}</span>
            </button>
          </div>
        </section>
      </div>
      <p v-else class="muted rail-empty">暂无月份</p>
    </aside>

    <main class="main">
      <section v-if="latest" class="card latest-card">
        <h2 class="card-title">
          最新日记
          <span class="chip">{{ formatTs(latest.created_ts) }}</span>
        </h2>
        <div class="latest-body">
          <div class="latest-text">
            <strong class="latest-title">{{ latest.title }}</strong>
            <p class="latest-preview">{{ latestPreview }}</p>
            <div class="tags">
              <span v-if="latest.mood" class="chip">{{ latest.mood }}</span>
              <span v-for="tag in latest.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
            </div>
          </div>
          <button type="button" class="btn more" @click="openEntry(latest)">阅读全文</button>
        </div>
      </section>

      <section class="card">
        <h2 class="card-title">日记</h2>
        <div class="toolbar">
          <input
            v-model="query"
            class="search"
            type="search"
            placeholder="搜索标题或正文…"
            aria-label="搜索日记"
          />
          <div class="tag-row">
            <button
              type="button"
              class="chip tag-btn"
              :class="{ 'is-active': !activeTag }"
              @click="activeTag = ''"
            >
              全部
            </button>
            <button
              v-for="tag in allTags"
              :key="tag"
              type="button"
              class="chip tag-btn"
              :class="{ 'is-active': activeTag === tag }"
              @click="activeTag = tag"
            >
              {{ tag }}
            </button>
          </div>
          <button
            v-if="query || activeTag"
            type="button"
            class="btn btn-ghost clear"
            @click="clearFilters"
          >
            清除筛选
          </button>
        </div>

        <div v-if="groups.length" class="months">
          <article
            v-for="group in groups"
            :key="group.label"
            :ref="(el) => setMonthRef(group.label, el)"
            class="month"
          >
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
        <p v-else class="muted empty">
          {{ query || activeTag ? "没有匹配的日记" : "暂无日记" }}
        </p>
      </section>
    </main>
  </div>

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
.diary-page {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: var(--page-gap);
  align-items: start;
}

.rail {
  position: sticky;
  top: 16px;
  padding: 14px 12px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: color-mix(in srgb, var(--md-sys-color-surface-container) 88%, transparent);
  border: 1px solid var(--md-sys-color-outline-variant);
}

.rail-title {
  margin: 0 0 12px;
  font: var(--md-sys-typescale-label);
  color: var(--md-sys-color-on-surface-variant);
}

.year-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.year-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.year-label {
  font: var(--md-sys-typescale-title);
  font-size: 1.05rem;
  padding: 8px 10px;
  border-radius: var(--md-sys-shape-corner-small);
  background: color-mix(in srgb, var(--md-sys-color-primary) 16%, transparent);
  color: var(--md-sys-color-primary);
  text-align: center;
}

.month-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.month-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid transparent;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  color: inherit;
  cursor: pointer;
  text-align: left;
  font-size: 0.9rem;
}

.month-chip:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.month-chip.is-active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.month-num {
  flex: 1;
  white-space: nowrap;
}

.month-count {
  opacity: 0.75;
  font-size: 0.8rem;
}

.rail-empty {
  margin: 0;
  font-size: 0.85rem;
}

.latest-card {
  margin-bottom: 0;
}

.latest-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

.latest-text {
  min-width: 0;
  flex: 1;
}

.latest-title {
  display: block;
  font: var(--md-sys-typescale-title);
  margin-bottom: 8px;
}

.latest-preview {
  margin: 0 0 12px;
  line-height: 1.7;
  color: var(--md-sys-color-on-surface-variant);
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.search {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--md-sys-shape-corner-full);
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface);
  color: inherit;
  font: inherit;
}

.search:focus {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: 1px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-btn {
  cursor: pointer;
  border: 1px solid transparent;
}

.tag-btn.is-active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.clear {
  align-self: flex-start;
}

.months {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.month {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
  background: color-mix(in srgb, var(--md-sys-color-surface) 92%, transparent);
  scroll-margin-top: 16px;
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
  flex-shrink: 0;
}

.month-head.is-open .caret {
  transform: rotate(225deg);
}

.month-body {
  padding: 0 16px 16px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 4px;
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
  gap: 12px;
}

.entry {
  padding: 14px 16px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container);
  border: 1px solid color-mix(in srgb, var(--md-sys-color-outline-variant) 70%, transparent);
}

.entry-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.clamped {
  margin: 10px 0;
  line-height: 1.65;
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
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.empty {
  margin: 0;
}

.main {
  display: flex;
  flex-direction: column;
  gap: var(--page-gap);
  min-width: 0;
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

@media (max-width: 800px) {
  .diary-page {
    grid-template-columns: minmax(0, 1fr);
  }

  .rail {
    position: static;
  }

  .month-grid {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .month-chip {
    flex: 1 1 120px;
  }

  .latest-body {
    flex-direction: column;
  }
}
</style>
