<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatTs } from "../utils/format"
import { resolveAssetUrl } from "../utils/url"

const store = useDashboard()
const shot = computed(() => store.status.value?.screenshot ?? null)
const thumbUrl = computed(() => resolveAssetUrl(shot.value?.url))
const closeButton = ref<HTMLButtonElement | null>(null)
const thumbFailed = ref(false)
let restoreFocus: HTMLElement | null = null

const canOpen = computed(() => Boolean(thumbUrl.value) && !thumbFailed.value)

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && store.lightboxOpen.value) {
    store.closeLightbox()
  }
}

function onThumbError(): void {
  thumbFailed.value = true
}

function onThumbLoad(): void {
  thumbFailed.value = false
}

/** 打开灯箱并把焦点移到关闭按钮 */
async function open(): Promise<void> {
  if (!canOpen.value) {
    return
  }
  restoreFocus = document.activeElement as HTMLElement | null
  store.openLightbox()
  await nextTick()
  closeButton.value?.focus()
}

/** 关闭灯箱并归还焦点 */
function close(): void {
  store.closeLightbox()
  restoreFocus?.focus()
  restoreFocus = null
}

watch(thumbUrl, () => {
  thumbFailed.value = false
})

watch(
  () => store.lightboxOpen.value,
  (openState) => {
    document.body.style.overflow = openState ? "hidden" : ""
  },
)

onMounted(() => window.addEventListener("keydown", onKeydown))
onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown)
  document.body.style.overflow = ""
})
</script>

<template>
  <section class="card">
    <h2 class="card-title">
      桌面快照
      <span v-if="shot" class="chip">{{ formatTs(shot.ts) }}</span>
    </h2>
    <button
      v-if="canOpen"
      type="button"
      class="thumb-btn"
      aria-label="查看桌面快照"
      @click="open"
    >
      <img
        class="thumb"
        :src="thumbUrl"
        alt="模糊桌面快照"
        loading="eager"
        @error="onThumbError"
        @load="onThumbLoad"
      />
      <span class="thumb-hint">点击放大</span>
    </button>
    <div v-else class="placeholder" :class="{ 'is-error': thumbFailed }">
      <span class="ph-icon" aria-hidden="true"></span>
      <p class="muted">{{ thumbFailed ? "快照加载失败" : "暂无快照" }}</p>
    </div>
  </section>

  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="store.lightboxOpen.value && shot && !thumbFailed"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-label="桌面快照"
        @click.self="close"
      >
        <figure class="dialog">
          <img class="full" :src="thumbUrl" alt="模糊桌面快照" />
          <figcaption class="muted">{{ formatTs(shot.ts) }}</figcaption>
        </figure>
        <button ref="closeButton" type="button" class="btn close-btn" @click="close">关闭</button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.thumb-btn {
  position: relative;
  display: block;
  width: 100%;
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
  border: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-high);
  padding: 0;
  cursor: zoom-in;
}

.thumb {
  display: block;
  width: 100%;
  height: 220px;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.thumb-btn:hover .thumb {
  transform: scale(1.01);
}

.thumb-hint {
  position: absolute;
  right: 10px;
  bottom: 10px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  color: var(--md-sys-color-on-surface);
  background: color-mix(in srgb, var(--md-sys-color-surface) 82%, transparent);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.thumb-btn:hover .thumb-hint {
  opacity: 1;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  border-radius: var(--md-sys-shape-corner-medium);
  border: 1px dashed var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-high);
}

.placeholder.is-error {
  border-color: var(--md-sys-color-error);
}

.ph-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background:
    linear-gradient(currentColor, currentColor) center / 22px 2px no-repeat,
    linear-gradient(currentColor, currentColor) center / 2px 22px no-repeat;
  color: var(--md-sys-color-outline);
  opacity: 0.75;
  transform: rotate(-45deg);
  mask: radial-gradient(circle at center, transparent 10px, #000 10.5px);
}

.placeholder p {
  margin: 0;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: color-mix(in srgb, var(--md-sys-color-surface) 40%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.dialog {
  margin: 0;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  animation: pop 0.18s ease;
}

.full {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: var(--md-sys-shape-corner-medium);
  box-shadow: var(--md-sys-elevation-2);
  background: var(--md-sys-color-surface-container);
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
