<template>
  <div class="card">
    <div class="tpl-top">
      <div>
        <h3>合同模板</h3>
        <p class="desc">AI 生成公平版本</p>
      </div>
      <div class="tpl-ctls">
        <select v-model="selected">
          <option value="">选择…</option>
          <option v-for="t in types" :key="t.key" :value="t.key">{{ t.name }}</option>
        </select>
        <button class="btn btn-primary" @click="generate" :disabled="!selected || loading" style="padding:9px 22px;font-size:14px">{{ loading ? '生成中' : '生成' }}</button>
      </div>
    </div>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="template" class="tpl-result fade-up">
      <div class="tpl-header">
        <span class="tpl-name">{{ templateName }}</span>
        <button class="btn" @click="copyTemplate" style="padding:6px 16px;font-size:12px">复制</button>
      </div>
      <pre class="tpl-text">{{ template }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const types = ref([]); const selected = ref(''); const loading = ref(false); const template = ref(''); const templateName = ref(''); const error = ref('')
onMounted(async () => {
  try {
    const res = await fetch('/api/templates')
    if (!res.ok) throw new Error('加载失败')
    types.value = await res.json()
  } catch (e) {
    error.value = '模板列表加载失败'
  }
})
async function generate() {
  loading.value = true; template.value = ''; error.value = ''
  try {
    const res = await fetch('/api/templates/generate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ type:selected.value }) })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || '生成失败') }
    const d = await res.json(); template.value = d.template; templateName.value = d.name
  } catch (e) {
    error.value = e.message || '生成失败'
  } finally {
    loading.value = false
  }
}
function copyTemplate() { navigator.clipboard.writeText(template.value) }
</script>

<style scoped>
.tpl-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.tpl-top h3 { font-size: 16px; font-weight: 600; }
.desc { font-size: 13px; color: var(--text3); margin-top: 2px; }
.tpl-ctls { display: flex; gap: 8px; }
.tpl-ctls select { padding: 9px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; font-size: 14px; color: var(--text); outline: none; }
.tpl-ctls select:focus { border-color: var(--accent); }
.tpl-result { margin-top: 22px; }
.tpl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.tpl-name { font-size: 14px; font-weight: 500; color: var(--green); }
.tpl-text { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 20px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; max-height: 360px; overflow-y: auto; color: var(--text2); }
.error-msg { padding: 12px; color: var(--red); font-size: 13px; text-align: center; margin-top: 12px; }
</style>
