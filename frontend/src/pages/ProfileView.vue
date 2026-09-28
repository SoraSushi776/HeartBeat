<script setup lang="ts">
import { computed } from "vue"
import GithubPanel from "../components/GithubPanel.vue"
import Heatmap from "../components/Heatmap.vue"
import TagsCard from "../components/TagsCard.vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()
const days = computed(() => store.github.value?.contributions?.days ?? [])
const showHeatmap = computed(() => store.site.value?.show_heatmap !== false)
</script>

<template>
  <div class="profile-grid">
    <div class="main">
      <GithubPanel />
    </div>
    <div class="side">
      <TagsCard />
    </div>
    <div v-if="showHeatmap" class="full">
      <Heatmap :days="days" />
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: var(--page-gap);
  align-items: stretch;
}

.main,
.side {
  min-width: 0;
  display: flex;
  flex-direction: column;
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
