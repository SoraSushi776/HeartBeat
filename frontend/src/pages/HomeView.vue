<script setup lang="ts">
import LiveStatus from "../components/LiveStatus.vue"
import MediaCard from "../components/MediaCard.vue"
import SnapshotLightbox from "../components/SnapshotLightbox.vue"
</script>

<template>
  <div class="home-grid">
    <div class="tile"><LiveStatus /></div>
    <div class="tile"><MediaCard /></div>
    <div class="tile"><SnapshotLightbox /></div>
  </div>
</template>

<style scoped>
.home-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--page-gap);
  align-items: stretch;
}

.tile {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.tile > :deep(.card) {
  height: 100%;
}

.tile-wide {
  grid-column: 1 / -1;
}

@media (max-width: 1100px) {
  .home-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .home-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
