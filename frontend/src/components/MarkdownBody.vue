<script setup lang="ts">
import { computed } from "vue"
import { renderMarkdown } from "../utils/markdown"

const props = defineProps<{ content: string }>()

const html = computed(() => renderMarkdown(props.content))
</script>

<template>
  <div class="md-body" v-html="html"></div>
</template>
