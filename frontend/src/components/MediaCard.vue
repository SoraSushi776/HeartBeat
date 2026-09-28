<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatDuration } from "../utils/format"

const store = useDashboard()
const media = computed(() => store.status.value?.media ?? null)

const displayPosition = ref(0)
let frame = 0

const STATE_TEXT: Record<string, string> = {
  playing: "正在播放",
  paused: "已暂停",
  idle: "暂无播放",
}

const stateText = computed(() => STATE_TEXT[media.value?.state ?? "idle"] ?? "暂无播放")

const progressRatio = computed(() => {
  const duration = media.value?.duration_ms ?? 0
  if (!duration || duration <= 0) {
    return 0
  }
  return Math.min(1, displayPosition.value / duration)
})

const bars = Array.from({ length: 28 }, (_, index) => ({
  height: 28 + ((index * 37) % 48),
  delay: `${(index % 7) * 0.12}s`,
}))

const playState = computed(() => (media.value?.state === "playing" ? "running" : "paused"))

function syncPosition(): void {
  displayPosition.value = media.value?.position_ms ?? 0
}

/** 按帧推进本地播放进度，服务端数据到达时校正 */
function tick(): void {
  if (media.value?.state === "playing") {
    displayPosition.value += 16
  }
  frame = requestAnimationFrame(tick)
}

watch(media, syncPosition)

onMounted(() => {
  syncPosition()
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
        <img v-if="media.cover_url" class="cover" :src="media.cover_url" alt="专辑封面" />
        <div v-else class="cover cover-empty"></div>
        <div class="wave" :style="{ '--play-state': playState }" aria-hidden="true">
          <span
            v-for="(bar, index) in bars"
            :key="index"
            class="bar"
            :style="{ height: `${bar.height}%`, animationDelay: bar.delay }"
          ></span>
        </div>
      </div>
      <div class="meta">
        <div class="title">{{ media.title || "未知曲目" }}</div>
        <div class="muted">{{ media.artist || "未知歌手" }}</div>
        <div class="muted sub">{{ media.album || media.app || "" }}</div>
        <div class="progress">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${progressRatio * 100}%` }"></div>
          </div>
          <div class="times muted">
            <span>{{ formatDuration(displayPosition) }}</span>
            <span>{{ formatDuration(media.duration_ms) }}</span>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="muted empty">当前没有在播音乐</p>
  </section>
</template>

<style scoped>
.media-body {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.cover-wrap {
  position: relative;
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

.wave {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  height: 28px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  padding: 4px 6px;
  border-radius: var(--md-sys-shape-corner-small);
  background: color-mix(in srgb, var(--md-sys-color-surface) 72%, transparent);
}

.bar {
  flex: 1;
  min-width: 2px;
  border-radius: 2px;
  background: var(--md-sys-color-primary);
  transform-origin: bottom;
  animation: wave 0.9s ease-in-out infinite alternate;
  animation-play-state: var(--play-state, paused);
  opacity: 0.9;
}

@keyframes wave {
  from {
    transform: scaleY(0.35);
  }
  to {
    transform: scaleY(1);
  }
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
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
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
