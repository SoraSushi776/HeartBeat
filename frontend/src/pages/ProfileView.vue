<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import GithubPanel from "../components/GithubPanel.vue"
import Heatmap from "../components/Heatmap.vue"
import ProcessCloud from "../components/ProcessCloud.vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()
const processCard = ref<HTMLElement | null>(null)
const processHeight = ref<number | null>(null)
let observer: ResizeObserver | null = null

const days = computed(() => store.github.value?.contributions?.days ?? [])

function measureProcess(): void {
  const node = processCard.value?.querySelector(".card") ?? processCard.value
  if (node instanceof HTMLElement) {
    processHeight.value = node.getBoundingClientRect().height
  }
}

onMounted(async () => {
  await nextTick()
  measureProcess()
  observer = new ResizeObserver(() => measureProcess())
  if (processCard.value) {
    observer.observe(processCard.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})

watch(
  () => store.status.value?.processes?.length ?? 0,
  async () => {
    await nextTick()
    measureProcess()
  },
)
</script>

<template>
  <div class="profile-grid">
    <div ref="processCard" class="side">
      <ProcessCloud />
    </div>
    <div class="main">
      <GithubPanel :compact-height="processHeight" />
    </div>
    <div class="full">
      <Heatmap :days="days" />
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: var(--page-gap);
  align-items: start;
}

.full {
  grid-column: 1 / -1;
}

@media (max-width: 1100px) {
  .profile-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
