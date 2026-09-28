<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()

const title = computed(() => store.site.value?.tags_title || "标签")
const tags = computed(() => store.site.value?.tags ?? [])
</script>

<template>
  <section class="card tags-card">
    <h2 class="card-title">{{ title }}</h2>
    <div v-if="tags.length" class="tag-list">
      <span v-for="tag in tags" :key="tag" class="chip tag">{{ tag }}</span>
    </div>
    <p v-else class="muted empty">暂无标签</p>
  </section>
</template>

<style scoped>
.tags-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-content: flex-start;
  flex: 1;
}

.tag {
  font-size: 0.95rem;
  padding: 10px 16px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--md-sys-color-primary-container) 70%, transparent);
  color: var(--md-sys-color-on-surface);
}

.empty {
  margin: 0;
}
</style>
