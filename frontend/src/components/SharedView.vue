<template>
  <div class="shared-page" v-if="data">
    <header class="app-header">
      <h1>📄 AI 合同风险扫描</h1>
      <p class="sub">分享的合同分析</p>
    </header>
    <Result :result="data" />
  </div>
  <div v-else-if="error" class="shared-error">
    <div class="card" style="text-align:center;padding:60px">
      <div style="font-size:40px;margin-bottom:12px">🔗</div>
      <div style="font-size:16px;color:var(--text2)">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Result from './Result.vue'
const data = ref(null)
const error = ref('')
onMounted(async () => {
  const id = window.location.pathname.split('/share/')[1]
  if (!id) { error.value = '链接无效'; return }
  try {
    const res = await fetch(`/api/shared/${id}`)
    if (!res.ok) throw new Error('链接已过期或不存在（7天有效）')
    data.value = await res.json()
  } catch (e) { error.value = e.message }
})
</script>
PYEOF