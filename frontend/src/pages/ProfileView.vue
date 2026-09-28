<script setup lang="ts">
import { computed } from "vue"
import GithubPanel from "../components/GithubPanel.vue"
import Heatmap from "../components/Heatmap.vue"
import ProcessCloud from "../components/ProcessCloud.vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()

const days = computed(() => store.github.value?.contributions?.days ?? [])
</script>

<template>
  <div class="profile-grid">
    <div class="side">
      <ProcessCloud />
    </div>
    <div class="main">
      <GithubPanel />
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
