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
    <main class="column">
      <LiveStatus />
      <MediaCard />
      <SnapshotLightbox />
      <ProcessCloud />
      <GithubPanel />
      <Heatmap :days="days" />
      <DiaryTimeline />
      <FriendLinks />
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: var(--page-max);
  margin: 0 auto;
  padding: 28px 16px 48px;
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

.column {
  display: flex;
  flex-direction: column;
  gap: var(--page-gap);
}

@media (max-width: 560px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
