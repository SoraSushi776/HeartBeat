<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { sanitizeHtml } from "../utils/sanitize"
import { formatTs } from "../utils/format"

const props = defineProps<{ compactHeight?: number | null }>()

const store = useDashboard()
const github = computed(() => store.github.value)
const collapsed = ref(false)

const readme = computed(() => {
  const html = github.value?.readme_html
  return html ? sanitizeHtml(html) : ""
})

const displayName = computed(() => github.value?.name || github.value?.login || "GitHub")

const compactStyle = computed(() => {
  if (!collapsed.value || !props.compactHeight) {
    return {}
  }
  return { minHeight: `${props.compactHeight}px` }
})

watch(
  () => props.compactHeight,
  () => {
    if (collapsed.value) {
      return
    }
  },
)
</script>

<template>
  <section class="card github-card" :class="{ 'is-collapsed': collapsed }" :style="compactStyle">
    <header class="head">
      <h2 class="card-title">GitHub</h2>
      <button type="button" class="btn btn-ghost toggle" @click="collapsed = !collapsed">
        {{ collapsed ? "展开" : "折叠" }}
      </button>
    </header>
    <div v-if="github" class="profile">
      <img v-if="github.avatar_url" class="avatar" :src="github.avatar_url" alt="GitHub 头像" />
      <div class="info">
        <a
          v-if="github.html_url"
          class="name"
          :href="github.html_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ displayName }}
        </a>
        <div v-else class="name">{{ displayName }}</div>
        <div v-if="github.bio" class="muted bio">{{ github.bio }}</div>
        <div v-if="github.contributions" class="muted stats">
          近一年贡献 {{ github.contributions.total_last_year }} 次
          <span v-if="github.fetched_ts"> · 更新于 {{ formatTs(github.fetched_ts) }}</span>
        </div>
      </div>
    </div>
    <div v-if="readme && !collapsed" class="readme" v-html="readme"></div>
    <p v-if="!github" class="muted empty">暂无 GitHub 资料</p>
    <p v-else-if="collapsed && readme" class="muted empty">已折叠 · 点击展开阅读 README</p>
  </section>
</template>

<style scoped>
.github-card {
  height: 100%;
  overflow: auto;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.toggle {
  flex-shrink: 0;
}

.profile {
  display: flex;
  gap: 16px;
  align-items: center;
  margin: 8px 0 16px;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
}

.info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.name {
  font: var(--md-sys-typescale-title);
  color: var(--md-sys-color-on-surface);
}

.bio,
.stats {
  font-size: 0.85rem;
}

.readme {
  overflow-x: auto;
  line-height: 1.7;
}

.readme :deep(h1),
.readme :deep(h2),
.readme :deep(h3) {
  margin: 1em 0 0.5em;
}

.empty {
  margin: 0;
}

.is-collapsed {
  overflow: hidden;
}
</style>
