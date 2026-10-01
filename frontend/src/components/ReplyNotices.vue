<script setup lang="ts">
import { useRouter } from "vue-router"
import { useDashboard } from "../stores/dashboard"
import { focusMessage, type ReplyNotice } from "../utils/replyNotify"

const store = useDashboard()
const router = useRouter()

/** 跳到留言页并定位到收到回复的那条留言 */
async function onOpen(notice: ReplyNotice): Promise<void> {
  store.dismissNotice(notice)
  await router.push("/messages")
  window.setTimeout(() => focusMessage(notice.message.id), 80)
}

/** 取第一条回复正文作为通知摘要 */
function preview(notice: ReplyNotice): string {
  const replies = notice.message.replies
  return replies && replies.length > 0 ? replies[0].content : ""
}
</script>

<template>
  <Teleport to="body">
    <div class="notice-stack">
      <article
        v-for="notice in store.notices.value"
        :key="notice.message.id"
        class="notice"
        @click="onOpen(notice)"
      >
        <header class="notice-head">
          <span class="notice-title">收到新回复</span>
          <button
            type="button"
            class="notice-close"
            aria-label="关闭通知"
            @click.stop="store.dismissNotice(notice)"
          >
            ×
          </button>
        </header>
        <p class="notice-body">{{ preview(notice) }}</p>
        <p class="notice-origin">原留言：{{ notice.message.content }}</p>
      </article>
    </div>
  </Teleport>
</template>

<style scoped>
.notice-stack {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 320px;
}

.notice {
  padding: 12px 14px;
  border-radius: var(--md-sys-shape-corner-medium);
  border-left: 3px solid var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-highest);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
  cursor: pointer;
  animation: notice-in 0.22s ease-out;
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.notice-title {
  font: var(--md-sys-typescale-label);
  color: var(--md-sys-color-primary);
}

.notice-close {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 4px;
  cursor: pointer;
  opacity: 0.7;
}

.notice-close:hover {
  opacity: 1;
}

.notice-body {
  margin: 8px 0 0;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.notice-origin {
  margin: 6px 0 0;
  font-size: 0.78rem;
  opacity: 0.7;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes notice-in {
  from {
    opacity: 0;
    transform: translateX(16px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 720px) {
  .notice-stack {
    left: 12px;
    right: 12px;
    max-width: none;
  }
}
</style>
