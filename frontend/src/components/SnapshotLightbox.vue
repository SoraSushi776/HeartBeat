<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatTs } from "../utils/format"

const store = useDashboard()
const shot = computed(() => store.status.value?.screenshot ?? null)
const closeButton = ref<HTMLButtonElement | null>(null)
let restoreFocus: HTMLElement | null = null

const canOpen = computed(() => Boolean(shot.value?.url))

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape" && store.lightboxOpen.value) {
    store.closeLightbox()
  }
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
      <img class="thumb" :src="shot?.url" alt="模糊桌面快照" />
    </button>
    <p v-else class="muted empty">暂无快照</p>
  </section>

  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="store.lightboxOpen.value && shot"
        class="overlay"
        role="dialog"
        aria-modal="true"
        aria-label="桌面快照"
        @click.self="close"
      >
        <figure class="dialog">
          <img class="full" :src="shot.url" alt="模糊桌面快照" />
          <figcaption class="muted">{{ formatTs(shot.ts) }}</figcaption>
        </figure>
        <button ref="closeButton" type="button" class="btn close-btn" @click="close">关闭</button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.thumb-btn {
  display: block;
  width: 100%;
  border-radius: var(--md-sys-shape-corner-medium);
  overflow: hidden;
}

.thumb {
  width: 100%;
  max-height: 280px;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.thumb-btn:hover .thumb {
  transform: scale(1.01);
}

.empty {
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
