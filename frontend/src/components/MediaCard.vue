<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatDuration } from "../utils/format"
import { resolveAssetUrl } from "../utils/url"

const store = useDashboard()
const media = computed(() => store.status.value?.media ?? null)

const displayPosition = ref(0)
const trackKey = ref("")
const coverVersion = ref(0)
let frame = 0
let lastTickTs = 0

const STATE_TEXT: Record<string, string> = {
  playing: "正在播放",
  paused: "已暂停",
  idle: "暂无播放",
}

const stateText = computed(() => STATE_TEXT[media.value?.state ?? "idle"] ?? "暂无播放")

const coverSrc = computed(() => {
  const base = resolveAssetUrl(media.value?.cover_url)
  if (!base) {
    return ""
  }
  const joiner = base.includes("?") ? "&" : "?"
  return `${base}${joiner}v=${coverVersion.value}`
})

const progressRatio = computed(() => {
  const duration = media.value?.duration_ms ?? 0
  if (!duration || duration <= 0) {
    return 0
  }
  return Math.min(1, displayPosition.value / duration)
})

function trackKeyOf(value: typeof media.value): string {
  return [value?.title, value?.artist, value?.album, value?.app].join("|")
}

function syncPosition(force = false): void {
  const nextKey = trackKeyOf(media.value)
  const incoming = media.value?.position_ms ?? 0
  const changed = nextKey !== trackKey.value
  if (changed || force) {
    if (changed && trackKey.value) {
      coverVersion.value += 1
    }
    trackKey.value = nextKey
    displayPosition.value = incoming
    return
  }
  if (incoming > 0) {
    displayPosition.value = incoming
    return
  }
  if (media.value?.state !== "playing") {
    displayPosition.value = Math.max(displayPosition.value, incoming)
  }
}

function tick(timestamp: number): void {
  const delta = lastTickTs ? timestamp - lastTickTs : 16
  lastTickTs = timestamp
  if (media.value?.state === "playing") {
    const duration = media.value?.duration_ms ?? 0
    const next = displayPosition.value + delta
    displayPosition.value = duration ? Math.min(next, duration) : next
  }
  frame = requestAnimationFrame(tick)
}

watch(media, () => syncPosition(false))

onMounted(() => {
  syncPosition(true)
  lastTickTs = 0
  frame = requestAnimationFrame(tick)
})

onUnmounted(() => cancelAnimationFrame(frame))
</script>

<template>
  <section class="card media-card">
    <h2 class="card-title">
      音乐
      <span class="chip">{{ stateText }}</span>
    </h2>
    <div v-if="media && media.state !== 'idle'" class="media-body">
      <div class="cover-wrap">
        <img v-if="coverSrc" class="cover" :src="coverSrc" alt="专辑封面" />
        <div v-else class="cover cover-empty"></div>
      </div>
      <div class="meta">
        <div class="title">{{ media.title || "未知曲目" }}</div>
        <div class="muted">{{ media.artist || "未知歌手" }}</div>
        <div class="muted sub">{{ media.album || media.app || "" }}</div>
      </div>
    </div>
    <div v-if="media && media.state !== 'idle'" class="progress">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${progressRatio * 100}%` }"></div>
      </div>
      <div class="times muted">
        <span>{{ formatDuration(displayPosition) }}</span>
        <span>{{ formatDuration(media.duration_ms) }}</span>
      </div>
    </div>
    <p v-else class="muted empty">当前没有在播音乐</p>
  </section>
</template>

<style scoped>
.media-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.media-body {
  display: flex;
  gap: 16px;
  align-items: center;
  flex: 1;
}

.cover-wrap {
  width: 112px;
  flex-shrink: 0;
}

.cover {
  width: 112px;
  height: 112px;
  object-fit: cover;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
}

.cover-empty {
  background: linear-gradient(135deg, var(--md-sys-color-primary-container), var(--md-sys-color-secondary-container));
}

.meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  font: var(--md-sys-typescale-title);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub {
  font-size: 0.82rem;
}

.progress {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.progress-track {
  height: 6px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--md-sys-color-primary);
}

.times {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
}

.empty {
  margin: 0;
}

@media (max-width: 560px) {
  .media-body {
    flex-direction: column;
  }

  .cover-wrap,
  .cover {
    width: 100%;
    height: auto;
    aspect-ratio: 1;
  }
}
</style>
