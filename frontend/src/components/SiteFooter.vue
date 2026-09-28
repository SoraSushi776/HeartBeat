<script setup lang="ts">
import { computed } from "vue"
import { useDashboard } from "../stores/dashboard"

const REPO_URL = "https://github.com/SoraSushi776/HeartBeat"

const store = useDashboard()

const friends = computed(() =>
  store.friends.value.slice().sort((a, b) => (a.sort ?? 0) - (b.sort ?? 0)),
)

const brand = computed(() => store.site.value.title || "HeartBeat")
const tagline = computed(() => store.site.value.tagline || "")
const showIcp = computed(() => store.site.value.show_icp === true)
const icpText = computed(() => store.site.value.icp_text || "萌ICP备20263011号")
const icpKeyword = computed(() => store.site.value.icp_keyword || "20263011")
const icpUrl = computed(
  () => `https://icp.gov.moe/?keyword=${encodeURIComponent(icpKeyword.value)}`,
)
</script>

<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="brand-col">
        <div class="brand-row">
          <svg class="gh-logo" viewBox="0 0 16 16" aria-hidden="true">
            <path
              fill="currentColor"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"
            />
          </svg>
          <span class="brand-name">{{ brand }}</span>
        </div>
        <p v-if="tagline" class="tagline">{{ tagline }}</p>
        <div class="link-stack">
          <a class="repo-link" :href="REPO_URL" target="_blank" rel="noopener noreferrer">
            <svg class="gh-logo gh-logo-sm" viewBox="0 0 16 16" aria-hidden="true">
              <path
                fill="currentColor"
                d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"
              />
            </svg>
            GitHub 仓库
          </a>
          <a
            v-if="showIcp"
            class="icp-link"
            :href="icpUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ icpText }}
          </a>
        </div>
      </div>
      <div class="links-col">
        <h3 class="col-title">友情链接</h3>
        <ul v-if="friends.length" class="link-list">
          <li v-for="friend in friends" :key="friend.id">
            <a :href="friend.url" target="_blank" rel="noopener noreferrer">{{ friend.name }}</a>
          </li>
        </ul>
        <p v-else class="muted empty">暂无友链</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  width: 100%;
  flex-shrink: 0;
  margin: 0;
  padding: 32px max(var(--page-pad-x), calc((100% - var(--page-max)) / 2 + var(--page-pad-x))) 28px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface-variant);
  box-sizing: border-box;
}

.footer-inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 28px 48px;
}

.brand-col {
  flex: 1 1 240px;
  min-width: 0;
  max-width: 420px;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--md-sys-color-on-surface);
}

.gh-logo {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.gh-logo-sm {
  width: 16px;
  height: 16px;
}

.brand-name {
  font: var(--md-sys-typescale-title);
  font-size: 1.15rem;
  letter-spacing: 0.02em;
}

.tagline {
  margin: 10px 0 0;
  font-size: 0.88rem;
  line-height: 1.6;
}

.link-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  margin-top: 14px;
}

.repo-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--md-sys-shape-corner-full);
  background: var(--md-sys-color-surface-container-high);
  color: var(--md-sys-color-on-surface);
  text-decoration: none;
  font: var(--md-sys-typescale-label);
  transition: background 0.15s ease;
}

.repo-link:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.icp-link {
  display: block;
  margin-top: 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.82rem;
  text-decoration: none;
  opacity: 0.9;
}

.icp-link:hover {
  color: var(--md-sys-color-primary);
  text-decoration: underline;
}

.links-col {
  flex: 0 1 auto;
  min-width: 160px;
}

.col-title {
  margin: 0 0 12px;
  font: var(--md-sys-typescale-label);
  color: var(--md-sys-color-on-surface);
  text-transform: none;
  letter-spacing: 0.04em;
}

.link-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.link-list a {
  color: var(--md-sys-color-on-surface-variant);
  text-decoration: none;
  font-size: 0.88rem;
  transition: color 0.15s ease;
}

.link-list a:hover {
  color: var(--md-sys-color-primary);
}

.empty {
  margin: 0;
  font-size: 0.85rem;
}

@media (max-width: 720px) {
  .footer-inner {
    flex-direction: column;
    gap: 22px;
  }

  .brand-col {
    max-width: none;
  }
}
</style>
