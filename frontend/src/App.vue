<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import LiveStatus from "./components/LiveStatus.vue"
import MediaCard from "./components/MediaCard.vue"
import ProcessCloud from "./components/ProcessCloud.vue"
import SnapshotLightbox from "./components/SnapshotLightbox.vue"
import GithubPanel from "./components/GithubPanel.vue"
import Heatmap from "./components/Heatmap.vue"
import DiaryTimeline from "./components/DiaryTimeline.vue"
import FriendLinks from "./components/FriendLinks.vue"
import { useDashboard, useDashboardLifecycle } from "./stores/dashboard"
import { resolveAssetUrl } from "./utils/url"

const store = useDashboard()
useDashboardLifecycle(store)

const theme = ref<"system" | "light" | "dark">("system")
const processCard = ref<HTMLElement | null>(null)
const processHeight = ref<number | null>(null)
let observer: ResizeObserver | null = null

const days = computed(() => store.github.value?.contributions?.days ?? [])
const backgroundStyle = computed(() => {
  const url = resolveAssetUrl(store.backgroundUrl.value)
  if (!url) {
    return {}
  }
  return {
    backgroundImage: `url(${url})`,
  }
})

const themeLabel = computed(
  () =>
    ({
      system: "主题：自动",
      light: "主题：浅色",
      dark: "主题：深色",
    })[theme.value],
)

const THEME_ORDER: Array<"system" | "light" | "dark"> = ["system", "light", "dark"]

function cycleTheme(): void {
  const index = THEME_ORDER.indexOf(theme.value)
  theme.value = THEME_ORDER[(index + 1) % THEME_ORDER.length]
  applyTheme()
}

function applyTheme(): void {
  const root = document.documentElement
  if (theme.value === "system") {
    root.removeAttribute("data-theme")
    return
  }
  root.setAttribute("data-theme", theme.value)
}

function measureProcess(): void {
  const node = processCard.value?.querySelector(".card") ?? processCard.value
  if (node instanceof HTMLElement) {
    processHeight.value = node.getBoundingClientRect().height
  }
}

onMounted(async () => {
  const saved = window.localStorage.getItem("heartbeat-theme")
  if (saved === "light" || saved === "dark" || saved === "system") {
    theme.value = saved
  }
  applyTheme()
  await nextTick()
  measureProcess()
  observer = new ResizeObserver(() => measureProcess())
  if (processCard.value) {
    observer.observe(processCard.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})

watch(
  () => store.status.value?.processes?.length ?? 0,
  async () => {
    await nextTick()
    measureProcess()
  },
)

function onThemeClick(): void {
  cycleTheme()
  window.localStorage.setItem("heartbeat-theme", theme.value)
}
</script>

<template>
  <div class="page-bg" :style="backgroundStyle"></div>
  <div class="page">
    <header class="header">
      <div>
        <h1 class="brand">HeartBeat</h1>
        <p class="muted tagline">个人主页与实时状态</p>
      </div>
      <div class="header-actions">
        <span v-if="store.demoMode.value" class="demo-badge">演示数据</span>
        <button type="button" class="btn btn-ghost" @click="onThemeClick">{{ themeLabel }}</button>
      </div>
    </header>
    <main class="dashboard">
      <div class="top-row">
        <div class="tile tile-live"><LiveStatus /></div>
        <div class="tile tile-media"><MediaCard /></div>
        <div class="tile tile-snapshot"><SnapshotLightbox /></div>
      </div>
      <div class="mid-row">
        <div ref="processCard" class="tile tile-process"><ProcessCloud /></div>
        <div class="tile tile-github">
          <GithubPanel :compact-height="processHeight" />
        </div>
      </div>
      <div class="tile tile-heatmap"><Heatmap :days="days" /></div>
      <div class="lower-row">
        <div class="tile tile-diary"><DiaryTimeline /></div>
        <div class="tile tile-friends"><FriendLinks /></div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--md-sys-color-surface) 88%, transparent), var(--md-sys-color-surface)),
    var(--md-sys-color-surface);
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  opacity: 1;
}

.page {
  max-width: var(--page-max);
  margin: 0 auto;
  padding: var(--page-pad-y) var(--page-pad-x) var(--page-pad-bottom);
}

.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.demo-badge {
  font-size: 0.78rem;
  padding: 4px 10px;
  border-radius: 999px;
  color: var(--md-sys-color-primary);
  background: color-mix(in srgb, var(--md-sys-color-primary) 14%, transparent);
}

.brand {
  margin: 0;
  font-size: 1.8rem;
  letter-spacing: 0.02em;
}

.tagline {
  margin: 4px 0 0;
}

.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--page-gap);
}

.top-row,
.mid-row,
.lower-row {
  display: grid;
  gap: var(--page-gap);
  align-items: stretch;
}

.top-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.mid-row {
  grid-template-columns: 5fr 7fr;
}

.lower-row {
  grid-template-columns: 7fr 5fr;
}

.tile {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.tile > :deep(.card),
.tile > :deep(section) {
  height: 100%;
}

.tile-heatmap {
  width: 100%;
}

@media (max-width: 1100px) {
  .top-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mid-row,
  .lower-row {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .top-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (orientation: landscape) and (max-height: 560px) {
  .page {
    padding-top: 12px;
  }

  .header {
    margin-bottom: 12px;
  }
}
</style>
