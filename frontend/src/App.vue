<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import LiveStatus from "./components/LiveStatus.vue"
import MediaCard from "./components/MediaCard.vue"
import ProcessCloud from "./components/ProcessCloud.vue"
import SnapshotLightbox from "./components/SnapshotLightbox.vue"
import GithubPanel from "./components/GithubPanel.vue"
import Heatmap from "./components/Heatmap.vue"
import DiaryTimeline from "./components/DiaryTimeline.vue"
import FriendLinks from "./components/FriendLinks.vue"
import { useDashboard, useDashboardLifecycle } from "./stores/dashboard"

const store = useDashboard()
useDashboardLifecycle(store)

const theme = ref<"system" | "light" | "dark">("system")

const days = computed(() => store.github.value?.contributions?.days ?? [])

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

onMounted(() => {
  const saved = window.localStorage.getItem("heartbeat-theme")
  if (saved === "light" || saved === "dark" || saved === "system") {
    theme.value = saved
  }
  applyTheme()
})

/** 切换主题并写入本地存储 */
function onThemeClick(): void {
  cycleTheme()
  window.localStorage.setItem("heartbeat-theme", theme.value)
}
</script>

<template>
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
      <div class="tile tile-live"><LiveStatus /></div>
      <div class="tile tile-media"><MediaCard /></div>
      <div class="tile tile-snapshot"><SnapshotLightbox /></div>
      <div class="tile tile-process"><ProcessCloud /></div>
      <div class="tile tile-github"><GithubPanel /></div>
      <div class="tile tile-heatmap"><Heatmap :days="days" /></div>
      <div class="tile tile-diary"><DiaryTimeline /></div>
      <div class="tile tile-friends"><FriendLinks /></div>
    </main>
  </div>
</template>

<style scoped>
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
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--page-gap);
  align-items: start;
}

.tile {
  min-width: 0;
}

.tile-live {
  grid-column: span 4;
}

.tile-media {
  grid-column: span 4;
}

.tile-snapshot {
  grid-column: span 4;
}

.tile-process {
  grid-column: span 5;
}

.tile-github {
  grid-column: span 7;
}

.tile-heatmap {
  grid-column: span 12;
}

.tile-diary {
  grid-column: span 7;
}

.tile-friends {
  grid-column: span 5;
}

@media (max-width: 1100px) {
  .dashboard {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .tile-live,
  .tile-media,
  .tile-snapshot,
  .tile-process {
    grid-column: span 3;
  }

  .tile-github,
  .tile-heatmap,
  .tile-diary,
  .tile-friends {
    grid-column: span 6;
  }
}

@media (max-width: 720px) {
  .dashboard {
    grid-template-columns: minmax(0, 1fr);
  }

  .tile-live,
  .tile-media,
  .tile-snapshot,
  .tile-process,
  .tile-github,
  .tile-heatmap,
  .tile-diary,
  .tile-friends {
    grid-column: auto;
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
