<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"
import { sanitizeHtml } from "../utils/sanitize"
import { formatTs } from "../utils/format"

const store = useDashboard()
const github = computed(() => store.github.value)

const readme = computed(() => {
  const html = github.value?.readme_html
  return html ? sanitizeHtml(html) : ""
})

const displayName = computed(() => github.value?.name || github.value?.login || "GitHub")
</script>

<template>
  <section class="card">
    <h2 class="card-title">GitHub</h2>
    <div v-if="github" class="profile">
      <img v-if="github.avatar_url" class="avatar" :src="github.avatar_url" alt="GitHub 头像" />
      <div class="info">
        <a v-if="github.html_url" class="name" :href="github.html_url" target="_blank" rel="noopener noreferrer">
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
    <div v-if="readme" class="readme" v-html="readme"></div>
    <p v-else class="muted empty">暂无 GitHub 资料</p>
  </section>
</template>

<style scoped>
.profile {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
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
  line-height: 1.3;
}

.readme :deep(img) {
  max-width: 100%;
  border-radius: var(--md-sys-shape-corner-small);
}

.readme :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
}

.readme :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.88em;
}

.readme :deep(table) {
  border-collapse: collapse;
  max-width: 100%;
}

.readme :deep(th),
.readme :deep(td) {
  border: 1px solid var(--md-sys-color-outline-variant);
  padding: 6px 10px;
}

.empty {
  margin: 0;
}
</style>
