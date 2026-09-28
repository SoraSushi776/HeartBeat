<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"

const store = useDashboard()

const friends = computed(() =>
  store.friends.value.slice().sort((a, b) => (a.sort ?? 0) - (b.sort ?? 0)),
)
</script>

<template>
  <section class="card">
    <h2 class="card-title">友情链接</h2>
    <div v-if="friends.length" class="friends">
      <a
        v-for="friend in friends"
        :key="friend.id"
        class="friend"
        :href="friend.url"
        target="_blank"
        rel="noopener noreferrer"
      >
        <img v-if="friend.avatar_url" class="avatar" :src="friend.avatar_url" alt="" />
        <div v-else class="avatar avatar-empty">{{ friend.name.slice(0, 1) }}</div>
        <div class="meta">
          <div class="name">{{ friend.name }}</div>
          <div v-if="friend.description" class="muted desc">{{ friend.description }}</div>
        </div>
      </a>
    </div>
    <p v-else class="muted empty">暂无友链</p>
  </section>
</template>

<style scoped>
.friends {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.friend {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  color: inherit;
  text-decoration: none;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.friend:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  text-decoration: none;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--md-sys-shape-corner-full);
  object-fit: cover;
  flex-shrink: 0;
}

.avatar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  font: var(--md-sys-typescale-title);
}

.meta {
  min-width: 0;
}

.name {
  font: var(--md-sys-typescale-label);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desc {
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty {
  margin: 0;
}
</style>
