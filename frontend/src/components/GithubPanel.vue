<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { sanitizeHtml } from "../utils/sanitize"
import { formatTs } from "../utils/format"

const store = useDashboard()
const github = computed(() => store.github.value)
const modalOpen = ref(false)
const closeButton = ref<HTMLButtonElement | null>(null)
let restoreFocus: HTMLElement | null = null

const readme = computed(() => {
  const html = github.value?.readme_html
  return html ? sanitizeHtml(html) : ""
})

const displayName = computed(() => github.value?.name || github.value?.login || "GitHub")

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && modalOpen.value) {
    closeModal()
  }
}

async function openModal(): Promise<void> {
  if (!readme.value) {
    return
  }
  restoreFocus = document.activeElement as HTMLElement | null
  modalOpen.value = true
  await nextTick()
  closeButton.value?.focus()
}

function closeModal(): void {
  modalOpen.value = false
  restoreFocus?.focus()
  restoreFocus = null
}

watch(modalOpen, (open) => {
  document.body.style.overflow = open ? "hidden" : ""
})

onMounted(() => window.addEventListener("keydown", onKeydown))
onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown)
  document.body.style.overflow = ""
})
</script>

<template>
  <section class="card github-card">
    <header class="head">
      <h2 class="card-title">GitHub</h2>
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
    <div v-if="readme" class="readme-wrap">
      <div class="readme readme-preview" v-html="readme"></div>
      <button type="button" class="btn btn-ghost more-btn" @click="openModal">阅读全文</button>
    </div>
    <p v-if="!github" class="muted empty">暂无 GitHub 资料</p>
  </section>

  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modalOpen && readme"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-label="GitHub README"
        @click.self="closeModal"
      >
        <div class="dialog">
          <header class="dialog-head">
            <h2 class="dialog-title">README</h2>
            <button ref="closeButton" type="button" class="btn close-btn" @click="closeModal">
              关闭
            </button>
          </header>
          <div class="readme dialog-body" v-html="readme"></div>
        </div>
      </div>
    </Transition>
  </Teleport>
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

.readme-wrap {
  position: relative;
}

.readme-preview {
  max-height: 220px;
  overflow: hidden;
  mask-image: linear-gradient(180deg, #000 60%, transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, #000 60%, transparent 100%);
}

.more-btn {
  margin-top: 4px;
  color: var(--md-sys-color-primary);
}

.empty {
  margin: 0;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: color-mix(in srgb, var(--md-sys-color-surface) 40%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.dialog {
  display: flex;
  flex-direction: column;
  width: min(820px, 92vw);
  max-height: 86vh;
  border-radius: var(--md-sys-shape-corner-large);
  background: var(--md-sys-color-surface-container);
  box-shadow: var(--md-sys-elevation-2);
  animation: pop 0.18s ease;
  overflow: hidden;
}

.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-title {
  margin: 0;
  font: var(--md-sys-typescale-title);
  color: var(--md-sys-color-on-surface);
}

.dialog-body {
  padding: 16px 20px 24px;
  overflow: auto;
  color: var(--md-sys-color-on-surface);
}

.close-btn {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

@keyframes pop {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
