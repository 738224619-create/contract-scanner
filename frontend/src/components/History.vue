<template>
  <div v-if="items.length" class="card">
    <div class="hist-top">
      <h3>历史记录</h3>
      <button v-if="selected.length === 2" class="btn btn-primary" @click="doCompare" style="padding:7px 18px;font-size:13px">对比分析</button>
    </div>
    <div class="hist-list">
      <div v-for="item in items" :key="item.id" :class="['hist-item', { on: isSelected(item.id) }]" @click="toggleSelect(item)">
        <span class="dot">{{ isSelected(item.id) ? '●' : '○' }}</span>
        <div class="info">
          <div class="name">{{ item.filename }}</div>
          <div class="meta">{{ item.created_at }}<span v-if="item.has_optimized" class="tag">已优化</span></div>
        </div>
        <a :href="`/api/export/${item.id}`" class="dl" @click.stop>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1v9M3 7l4 4 4-4M1 12h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
      </div>
    </div>
    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="diff" class="diff-box fade-up">
      <div class="diff-title">{{ diff.filename1 }} ↔ {{ diff.filename2 }}</div>
      <div v-for="(d,i) in diff.diff" :key="i" :class="['diff-row', d.type]">
        <span class="diff-icon">{{ { changed:'↔', added:'+', removed:'−', same:'·' }[d.type] }}</span>
        <span class="diff-txt">{{ d.clause }}</span>
        <span v-if="d.risk1" :class="['badge','badge-'+d.risk1.risk_level]" style="margin-left:4px">{{ d.risk1.risk_level }}</span>
        <span v-if="d.type==='changed' && d.risk2" :class="['badge','badge-'+d.risk2.risk_level]" style="margin-left:4px">{{ d.risk2.risk_level }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
const p = defineProps({ refresh: Number })
const items = ref([]); const selected = ref([]); const diff = ref(null); const error = ref('')
async function fetchData() {
  try {
    const res = await fetch('/api/history')
    if (!res.ok) throw new Error('加载失败')
    items.value = await res.json()
    error.value = ''
  } catch (e) {
    error.value = '历史记录加载失败'
  }
}
function isSelected(id) { return selected.value.includes(id) }
function toggleSelect(item) {
  const i = selected.value.indexOf(item.id)
  if (i >= 0) selected.value.splice(i, 1)
  else if (selected.value.length < 2) selected.value.push(item.id)
  else selected.value = [item.id]
  if (selected.value.length !== 2) diff.value = null
}
async function doCompare() {
  try {
    const res = await fetch(`/api/compare?id1=${selected.value[0]}&id2=${selected.value[1]}`)
    if (!res.ok) throw new Error('对比失败')
    diff.value = await res.json()
  } catch (e) {
    alert('对比失败，请重试')
  }
}
onMounted(fetchData)
watch(() => p.refresh, fetchData)
</script>

<style scoped>
.hist-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.hist-top h3 { font-size: 16px; font-weight: 600; }
.hist-list { display: flex; flex-direction: column; gap: 4px; }
.hist-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 10px; cursor: pointer; transition: background .15s; }
.hist-item:hover { background: var(--surface2); }
.hist-item.on { background: rgba(124,92,252,.06); }
.dot { font-size: 11px; color: var(--text3); flex-shrink: 0; transition: color .2s; }
.hist-item.on .dot { color: var(--accent); }
.info { flex: 1; min-width: 0; }
.name { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { font-size: 12px; color: var(--text3); display: flex; align-items: center; gap: 8px; margin-top: 1px; }
.tag { font-size: 10px; background: rgba(52,211,153,.1); color: var(--green); padding: 1px 6px; border-radius: 6px; }
.dl { color: var(--text3); flex-shrink: 0; transition: color .2s; }
.dl:hover { color: var(--accent); }
.diff-box { margin-top: 14px; padding: 16px; background: var(--surface2); border-radius: var(--radius-xs); }
.diff-title { font-size: 13px; color: var(--text2); margin-bottom: 10px; }
.diff-row { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; }
.diff-row.changed { background: rgba(251,191,36,.05); }
.diff-row.added { background: rgba(52,211,153,.05); }
.diff-row.removed { background: rgba(248,113,113,.05); }
.diff-row.same { opacity: .35; }
.diff-icon { flex-shrink: 0; width: 16px; text-align: center; font-weight: 600; }
.diff-txt { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text2); }
.error-msg { padding: 12px; color: var(--red); font-size: 13px; text-align: center; }
</style>
