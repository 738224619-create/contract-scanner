<template>
  <div class="card result-card fade-up">
    <div class="result-top">
      <div>
        <div class="result-filename">{{ result.filename }}</div>
        <div v-if="result.scoring" class="result-meta">
          {{ result.scoring.risk_counts.high }} 高 · {{ result.scoring.risk_counts.medium }} 中 · {{ result.scoring.risk_counts.low }} 低
        </div>
      </div>
      <div class="result-btns" v-if="result.id">
        <button v-if="!optimizing && !optimized" class="btn btn-success" @click="doOptimize">优化合同</button>
        <button v-if="optimizing" class="btn" disabled>优化中…</button>
        <button class="btn" @click="doShare">分享</button>
        <a v-if="!optimized" :href="`/api/export/${result.id}`" class="btn" download>导出报告</a>
        <a v-if="optimized" :href="`/api/export/${result.id}?type=optimized`" class="btn btn-primary" download>下载优化版</a>
      </div>
    </div>

    <div v-if="result.scoring" class="score-row">
      <div class="score-gauge">
        <svg width="90" height="90" viewBox="0 0 90 90">
          <circle cx="45" cy="45" r="38" fill="none" :stroke="scoreRing" stroke-width="4" opacity=".15" />
          <circle cx="45" cy="45" r="38" fill="none" :stroke="scoreRing" stroke-width="4"
            :stroke-dasharray="239" :stroke-dashoffset="239 - (239 * result.scoring.total_score / 100)"
            stroke-linecap="round" transform="rotate(-90 45 45)" style="transition: stroke-dashoffset 1s ease" />
          <text x="45" y="42" text-anchor="middle" font-size="24" font-weight="700" :fill="scoreRing">{{ result.scoring.total_score }}</text>
          <text x="45" y="58" text-anchor="middle" font-size="11" fill="var(--text3)">/ 100</text>
        </svg>
        <div class="score-label">{{ result.scoring.verdict }}</div>
      </div>
      <div class="score-dims">
        <div v-for="d in result.scoring.dimensions" :key="d.name" class="dim">
          <span class="dim-label">{{ d.name }}</span>
          <div class="dim-track">
            <div class="dim-fill" :style="{ width: d.score + '%', background: d.score < 50 ? 'var(--red)' : d.score < 75 ? 'var(--orange)' : 'var(--green)' }"></div>
          </div>
          <span class="dim-val">{{ d.score }}</span>
        </div>
      </div>
      <RadarChart :dimensions="result.scoring.dimensions" />
    </div>

    <div v-if="shareUrl" class="share-bar fade-up">
      <input :value="shareUrl" readonly @click="$event.target.select()" />
      <button class="btn btn-primary" @click="copyShare" style="padding:8px 18px;font-size:13px">{{ copied ? '已复制' : '复制链接' }}</button>
    </div>

    <div class="summary-text">{{ result.summary }}</div>

    <div class="risk-list">
      <div v-for="(r, i) in result.risks" :key="i" :class="['risk-card', r.risk_level]">
        <div class="risk-card-top">
          <span :class="['badge', 'badge-'+r.risk_level]">
            {{ { low:'低风险', medium:'中风险', high:'高风险' }[r.risk_level] }}
          </span>
          <div class="confidence">
            <span class="conf-label">置信度</span>
            <div class="conf-track">
              <div class="conf-fill" :style="{ width: r.confidence + '%', background: r.confidence > 80 ? 'var(--green)' : r.confidence > 60 ? 'var(--orange)' : 'var(--red)' }"></div>
            </div>
            <span class="conf-num">{{ r.confidence }}%</span>
          </div>
        </div>
        <blockquote>{{ r.clause }}</blockquote>
        <p style="margin-top:12px;font-size:15px;line-height:1.7;color:var(--text2)"><span style="color:var(--text);font-weight:500">解释</span>　{{ r.explanation }}</p>
        <p style="margin-top:8px;font-size:15px;line-height:1.7;color:var(--text2)"><span style="color:var(--green);font-weight:500">建议</span>　{{ r.suggestion }}</p>
      </div>
    </div>

    <div v-if="optimized" class="opt-section fade-up">
      <div class="opt-header">
        <h3>优化后合同</h3>
        <span class="opt-badge">AI 修订</span>
      </div>
      <pre class="opt-text">{{ optimized }}</pre>
    </div>

    <ChatPanel v-if="result.id" :aid="result.id" :visible="!!result.id" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import RadarChart from './RadarChart.vue'
import ChatPanel from './ChatPanel.vue'
const props = defineProps({ result: Object })
const optimizing = ref(false)
const optimized = ref('')
const shareUrl = ref('')
const copied = ref(false)
const scoreRing = computed(() => {
  const s = props.result?.scoring?.total_score ?? 100
  return s < 50 ? 'var(--red)' : s < 65 ? 'var(--orange)' : s < 80 ? '#f59e0b' : 'var(--green)'
})
watch(() => props.result, (v) => { if (v?.optimized) optimized.value = v.optimized }, { immediate: true })
async function doOptimize() {
  if (!props.result?.id) return
  optimizing.value = true
  try { optimized.value = (await (await fetch(`/api/optimize/${props.result.id}`, { method:'POST' })).json()).optimized }
  catch { alert('优化失败') }
  finally { optimizing.value = false }
}
async function doShare() {
  if (!props.result?.id) return
  shareUrl.value = window.location.origin + (await (await fetch(`/api/share/${props.result.id}`, { method:'POST' })).json()).url
}
function copyShare() { navigator.clipboard.writeText(shareUrl.value); copied.value = true; setTimeout(() => copied.value = false, 2000) }
</script>

<style scoped>
.result-filename { font-size: 20px; font-weight: 600; letter-spacing: -.02em; }
.result-meta { font-size: 13px; color: var(--text3); margin-top: 4px; }
.result-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }
.result-btns { display: flex; gap: 8px; flex-wrap: wrap; }

.score-row { display: flex; gap: 32px; align-items: center; margin-bottom: 32px; padding: 24px; background: var(--surface2); border-radius: var(--radius-xs); flex-wrap: wrap; }
.score-gauge { text-align: center; flex-shrink: 0; }
.score-label { font-size: 13px; color: var(--text3); margin-top: 8px; }
.score-dims { flex: 1; min-width: 180px; }
.dim { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.dim-label { width: 48px; font-size: 13px; color: var(--text2); text-align: right; flex-shrink: 0; }
.dim-track { flex: 1; height: 5px; background: var(--surface3); border-radius: 3px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 3px; transition: width .6s cubic-bezier(.16,1,.3,1); }
.dim-val { width: 24px; font-size: 13px; text-align: right; font-weight: 600; }

.risk-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.confidence { display: flex; align-items: center; gap: 6px; }
.conf-label { font-size: 11px; color: var(--text3); }
.conf-track { width: 80px; height: 4px; background: var(--surface3); border-radius: 2px; overflow: hidden; }
.conf-fill { height: 100%; border-radius: 2px; transition: width .5s ease; }
.conf-num { font-size: 11px; font-weight: 600; color: var(--text2); width: 30px; }

.share-bar { display: flex; gap: 8px; margin-bottom: 20px; padding: 12px 16px; background: rgba(124,92,252,.06); border-radius: var(--radius-xs); border: 1px solid rgba(124,92,252,.1); }
.share-bar input { flex:1; padding:8px 12px; background:var(--surface); border:1px solid var(--border); border-radius:8px; font-size:13px; color:var(--text); outline:none; }
.share-bar input:focus { border-color: var(--accent); }

.summary-text { font-size: 15px; color: var(--text2); line-height: 1.7; margin-bottom: 28px; }

.opt-section { margin-top: 32px; padding-top: 28px; border-top: 1px solid var(--border); }
.opt-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.opt-header h3 { font-size: 17px; font-weight: 600; }
.opt-badge { font-size: 11px; background: rgba(52,211,153,.12); color: var(--green); padding: 2px 8px; border-radius: 6px; font-weight: 600; }
.opt-text { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 20px; font-size: 14px; line-height: 1.7; white-space: pre-wrap; max-height: 360px; overflow-y: auto; color: var(--text2); }
</style>
