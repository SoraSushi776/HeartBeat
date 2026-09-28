<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import SiteFooter from "./components/SiteFooter.vue"
import { NAV_ITEMS } from "./router"
import { useDashboard, useDashboardLifecycle } from "./stores/dashboard"
import { resolveAssetUrl } from "./utils/url"

const store = useDashboard()
useDashboardLifecycle(store)

const route = useRoute()
const navRouter = useRouter()
const theme = ref<"system" | "light" | "dark">("system")

const siteTitle = computed(() => store.site.value.title || "HeartBeat")
const siteTagline = computed(() => store.site.value.tagline || "")

const backgroundStyle = computed(() => {
  const url = resolveAssetUrl(store.backgroundUrl.value)
  if (!url) {
    return {}
  }
  return { backgroundImage: `url(${url})` }
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

function onThemeClick(): void {
  cycleTheme()
  window.localStorage.setItem("heartbeat-theme", theme.value)
}

function go(path: string): void {
  void navRouter.push(path)
}

onMounted(() => {
  const saved = window.localStorage.getItem("heartbeat-theme")
  if (saved === "light" || saved === "dark" || saved === "system") {
    theme.value = saved
  }
  applyTheme()
})
</script>

<template>
  <div class="page-bg" :style="backgroundStyle"></div>
  <div class="page">
    <header class="header">
      <div>
        <h1 class="brand">{{ siteTitle }}</h1>
        <p class="muted tagline">{{ siteTagline }}</p>
      </div>
      <div class="header-actions">
        <span v-if="store.demoMode.value" class="demo-badge">演示数据</span>
        <button type="button" class="btn btn-ghost" @click="onThemeClick">{{ themeLabel }}</button>
      </div>
    </header>
    <nav class="nav-tabs" aria-label="主导航">
      <button
        v-for="item in NAV_ITEMS"
        :key="item.name"
        type="button"
        class="tab"
        :class="{ 'is-active': route.name === item.name || route.path === item.path }"
        @click="go(item.path)"
      >
        {{ item.title }}
      </button>
    </nav>
    <main class="content">
      <RouterView />
    </main>
  </div>
  <SiteFooter />
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
}

.page {
  max-width: var(--page-max);
  margin: 0 auto;
  padding: var(--page-pad-y) var(--page-pad-x) 28px;
}

.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
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

.nav-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}

.tab {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 8px 16px;
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.tab:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.tab.is-active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.content {
  min-height: 50vh;
}

@media (max-width: 720px) {
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
    margin-bottom: 10px;
  }
}
</style>
