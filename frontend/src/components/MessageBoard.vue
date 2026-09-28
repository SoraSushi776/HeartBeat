<script setup lang="ts">
import { computed, ref } from "vue"
import { useDashboard } from "../stores/dashboard"
import { formatRelative } from "../utils/format"

const store = useDashboard()

const author = ref("")
const content = ref("")
const sending = ref(false)
const error = ref("")

const canSend = computed(() => store.isOnline.value && !sending.value && content.value.trim().length > 0)

const offlineHint = computed(() => (store.isOnline.value ? "" : "客户端离线，暂时无法发送留言"))

const messages = computed(() => store.messages.value.slice())

async function onSubmit(): Promise<void> {
  if (!canSend.value) {
    return
  }
  sending.value = true
  error.value = ""
  try {
    await store.sendMessage(author.value.trim(), content.value.trim())
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
    </form>
    <ul v-if="messages.length" class="message-list">
      <li v-for="message in messages" :key="message.id" class="message">
        <div class="message-head">
          <span class="author">{{ message.author || "匿名" }}</span>
          <span class="muted time">{{ formatRelative(message.created_ts, store.nowMs.value) }}</span>
        </div>
        <p class="body">{{ message.content }}</p>
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

.time {
  font-size: 0.78rem;
  flex-shrink: 0;
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
