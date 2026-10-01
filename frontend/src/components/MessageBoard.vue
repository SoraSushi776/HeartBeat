<script setup lang="ts">
import { computed, ref } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatRelative } from "../utils/format"

const store = useDashboard()

const author = ref("")
const content = ref("")
const exposeIp = ref(false)
const showLocation = ref(false)
const sending = ref(false)
const error = ref("")

const canSend = computed(() => store.isOnline.value && !sending.value && content.value.trim().length > 0)

const offlineHint = computed(() => (store.isOnline.value ? "" : "客户端离线，暂时无法发送留言"))

const messages = computed(() => store.messages.value.slice())

function locationOf(location: string | null | undefined): string {
  return location && location.trim() ? location : "未知"
}

async function onSubmit(): Promise<void> {
  if (!canSend.value) {
    return
  }
  sending.value = true
  error.value = ""
  try {
    await store.sendMessage(author.value.trim(), content.value.trim(), exposeIp.value)
    content.value = ""
  } catch (err) {
    error.value = err instanceof Error ? err.message : "发送失败"
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <section class="card">
    <h2 class="card-title">留言板</h2>
    <form class="composer" @submit.prevent="onSubmit">
      <input
        v-model="author"
        class="input author-input"
        type="text"
        maxlength="50"
        placeholder="昵称（可选，留空为匿名）"
        :disabled="!store.isOnline.value"
      />
      <textarea
        v-model="content"
        class="input content-input"
        rows="3"
        maxlength="500"
        placeholder="想说的话…"
        :disabled="!store.isOnline.value"
      />
      <div class="composer-foot">
        <span class="muted hint">{{ offlineHint || error }}</span>
        <button type="submit" class="btn" :disabled="!canSend">发送</button>
      </div>
      <label class="check">
        <input v-model="exposeIp" type="checkbox" :disabled="!store.isOnline.value" />
        <span>公开我的 IP 属地</span>
      </label>
    </form>
    <label class="check list-toggle">
      <input v-model="showLocation" type="checkbox" />
      <span>显示 IP 属地</span>
    </label>
    <ul v-if="messages.length" class="message-list">
      <li v-for="message in messages" :id="`message-${message.id}`" :key="message.id" class="message">
        <div class="message-head">
          <span class="author">{{ message.author || "匿名" }}</span>
          <span class="meta">
            <span v-if="showLocation && message.expose_ip" class="muted location">
              {{ locationOf(message.location) }}
            </span>
            <span class="muted time">{{ formatRelative(message.created_ts, store.nowMs.value) }}</span>
          </span>
        </div>
        <p class="body">{{ message.content }}</p>
        <ul v-if="message.replies?.length" class="reply-list">
          <li v-for="reply in message.replies" :key="reply.id" class="reply">
            <span class="reply-badge">回复</span>
            <span class="reply-body">{{ reply.content }}</span>
            <span class="muted reply-time">
              {{ formatRelative(reply.created_ts, store.nowMs.value) }}
            </span>
          </li>
        </ul>
      </li>
    </ul>
    <p v-else class="muted empty">暂无留言</p>
  </section>
</template>

<style scoped>
.composer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--md-sys-color-outline-variant, rgba(128, 128, 128, 0.35));
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  color: inherit;
  font: inherit;
  box-sizing: border-box;
}

.input:disabled {
  opacity: 0.55;
}

.content-input {
  resize: vertical;
  min-height: 72px;
}

.composer-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hint {
  font-size: 0.8rem;
  min-height: 1.2em;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  user-select: none;
}

.list-toggle {
  margin-bottom: 12px;
}

.message-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  padding: 12px;
  border-radius: var(--md-sys-shape-corner-medium);
  background: var(--md-sys-color-surface-container-high);
  transition: box-shadow 0.25s ease;
}

.message.is-highlighted {
  box-shadow: 0 0 0 2px var(--md-sys-color-primary);
}

.reply-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 10px;
  border-left: 2px solid var(--md-sys-color-primary);
  border-radius: 6px;
  background: var(--md-sys-color-surface-container-highest);
}

.reply-badge {
  flex-shrink: 0;
  font-size: 0.72rem;
  padding: 1px 6px;
  border-radius: 999px;
  color: var(--md-sys-color-on-primary);
  background: var(--md-sys-color-primary);
}

.reply-body {
  flex: 1;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.reply-time {
  flex-shrink: 0;
  font-size: 0.75rem;
}

.message-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.author {
  font: var(--md-sys-typescale-label);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
}

.location,
.time {
  font-size: 0.78rem;
}

.body {
  margin: 0;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.empty {
  margin: 0;
}
</style>
