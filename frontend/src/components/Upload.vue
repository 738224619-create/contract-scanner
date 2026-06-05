<template>
  <div class="card upload-card">
    <div v-if="!loading" class="drop-zone" @drop.prevent="onDrop" @dragover.prevent @click="triggerInput">
      <input type="file" ref="input" @change="onFile" accept=".pdf,.docx,.doc,.txt" hidden />
      <div class="dz-glow"></div>
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none" class="dz-svg">
        <rect x="2" y="6" width="52" height="44" rx="6" stroke="url(#g)" stroke-width="1.5" stroke-dasharray="6 4" />
        <path d="M20 28l8-8 8 8M28 20v20" stroke="url(#g)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        <defs><linearGradient id="g" x1="0" y1="0" x2="56" y2="56"><stop stop-color="#7c5cfc"/><stop offset="1" stop-color="#4f46e5"/></linearGradient></defs>
      </svg>
      <div class="dz-text">{{ file ? file.name : '拖拽合同文件' }}</div>
      <div class="dz-hint">{{ file ? '' : 'PDF · Word · TXT' }}</div>
      <div v-if="!file" class="dz-link" @click.stop="useSample">
        <span class="dz-link-text">试试示例合同</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4 2l4 4-4 4" stroke="#a78bfa" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
    </div>

    <div v-else class="loading-state">
      <div class="spinner"></div>
      <div class="loading-label">{{ progressText }}</div>
      <div class="loading-steps">
        <span v-for="s in steps" :key="s.key" :class="['step', { active: s.active, done: s.done }]">
          <span class="step-dot"></span>
          {{ s.label }}
        </span>
      </div>
    </div>

    <div v-if="error" class="error-bar">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
const emit = defineEmits(['analyzing', 'result'])
const loading = ref(false); const error = ref(''); const file = ref(null); const input = ref(null); const progressText = ref('')
const steps = reactive([
  { key: 'split', label: '拆分', active: false, done: false },
  { key: 'rules', label: '扫描', active: false, done: false },
  { key: 'laws',  label: '匹配', active: false, done: false },
  { key: 'ai',    label: '分析', active: false, done: false },
])
const s = `房屋租赁合同

出租方（甲方）：张三
承租方（乙方）：李四

一、租期：一年，自2026年1月1日至2026年12月31日。
二、租金：每月3000元，每月5日前支付。逾期每日按日租金的50%支付违约金。
三、押金：6000元。期满无息退还，但房屋有任何损坏，甲方有权全额扣除押金。
四、甲方对房屋内发生的任何人身伤害、财产损失概不负责。
五、甲方有权随时解除合同，仅需提前3日通知。乙方提前解约，押金不退并支付三个月违约金。`

async function upload(f) {
  file.value = f; loading.value = true; error.value = ''; progressText.value = '准备中'
  steps.forEach(x => { x.active = false; x.done = false })
  emit('analyzing', true); emit('result', null)
  const fd = new FormData(); fd.append('file', f)
  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: fd })
    const r = res.body.getReader(); const d = new TextDecoder(); let b = ''
    while (true) {
      const { done, value } = await r.read(); if (done) break
      b += d.decode(value, { stream: true })
      for (const line of b.split('\n')) {
        b = b.includes('\n') ? b.split('\n').pop() : ''
        if (!line.startsWith('data: ')) continue
        const ev = JSON.parse(line.slice(6))
        if (ev.type === 'progress') {
          progressText.value = ev.detail
          const sx = steps.find(x => x.key === ev.step)
          if (sx) { steps.forEach(x => x.active = false); sx.active = true }
          if (ev.step === 'done') steps.forEach(x => { x.active = false; x.done = true })
          const i = steps.findIndex(x => x.key === ev.step)
          for (let j = 0; j < i; j++) steps[j].done = true
        }
        if (ev.type === 'result') emit('result', ev.data)
      }
    }
  } catch (e) { error.value = e.message }
  finally { loading.value = false; emit('analyzing', false) }
}
async function useSample() { const b = new Blob([s], { type: 'text/plain' }); await upload(new File([b], '示例合同.txt', { type: 'text/plain' })) }
function triggerInput() { input.value?.click() }
function onFile(e) { const f = e.target.files[0]; if (f) upload(f) }
function onDrop(e) { const f = e.dataTransfer.files[0]; if (f) upload(f) }
</script>

<style scoped>
.upload-card { padding: 0; overflow: hidden; position: relative; }
.drop-zone { padding: 64px 40px; text-align: center; cursor: pointer; position: relative; }
.dz-glow {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 200px; height: 200px; border-radius: 50%;
  background: radial-gradient(circle, rgba(124,92,252,.06), transparent);
  pointer-events: none; transition: opacity .3s;
}
.drop-zone:hover .dz-glow { opacity: 1; }
.dz-svg { opacity: .6; margin-bottom: 16px; transition: opacity .3s; }
.drop-zone:hover .dz-svg { opacity: .9; }
.dz-text { font-size: 18px; font-weight: 500; color: var(--text); }
.dz-hint { font-size: 14px; color: var(--text3); margin-top: 4px; }
.dz-link { margin-top: 14px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; }
.dz-link-text { font-size: 14px; color: var(--accent2); transition: color .2s; }
.dz-link:hover .dz-link-text { color: #c4b5fd; }

.loading-state { padding: 56px 40px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 20px; }
.loading-label { font-size: 16px; color: var(--text); font-weight: 500; }
.loading-steps { display: flex; gap: 32px; }
.step { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text3); transition: color .3s; }
.step-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--surface3); transition: all .3s; }
.step.active { color: var(--accent2); }
.step.active .step-dot { background: var(--accent); box-shadow: 0 0 0 5px rgba(124,92,252,.15); animation: pulse 2s infinite; }
.step.done { color: var(--green); }
.step.done .step-dot { background: var(--green); }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 5px rgba(124,92,252,.15)} 50%{box-shadow:0 0 0 10px rgba(124,92,252,.05)} }

.error-bar { padding: 14px 24px; color: var(--red); font-size: 14px; text-align: center; background: rgba(248,113,113,.06); border-top: 1px solid rgba(248,113,113,.1); }
</style>
