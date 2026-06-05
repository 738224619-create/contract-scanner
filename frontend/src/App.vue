<template>
  <div v-if="isShared"><SharedView /></div>
  <div v-else>
    <header class="app-header">
      <div class="logo">合同卫士</div>
      <p>AI 驱动的合同风险分析</p>
    </header>
    <Upload @analyzing="onAnalyzing" @result="onResult" :loading="loading" />
    <Result v-if="result" :result="result" />
    <History @select="onHistorySelect" :refresh="historyKey" />
    <div class="divider-text">智能模板</div>
    <Templates />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Upload from './components/Upload.vue'
import Result from './components/Result.vue'
import History from './components/History.vue'
import SharedView from './components/SharedView.vue'
import Templates from './components/Templates.vue'

const isShared = computed(() => window.location.pathname.startsWith('/share/'))
const loading = ref(false)
const result = ref(null)
const historyKey = ref(0)

function onAnalyzing(v) { loading.value = v }
function onResult(r) { result.value = r; historyKey.value++ }
function onHistorySelect(record) {
  result.value = {
    id: record.id, filename: record.filename,
    risks: record.risks, summary: record.summary,
    optimized: record.optimized_text,
  }
}
</script>

<style scoped>
.logo-icon { -webkit-text-fill-color: initial; }
</style>
