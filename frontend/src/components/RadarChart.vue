<template>
  <svg viewBox="-105 -105 210 210" class="radar">
    <circle v-for="r in [20,40,60]" :key="r" :r="r" fill="none" stroke="var(--surface3)" stroke-width=".75" />
    <line v-for="(_,i) in dims" :key="i" :x1="0" :y1="0" :x2="76*Math.cos(a(i))" :y2="76*Math.sin(a(i))" stroke="var(--surface3)" stroke-width=".75" />
    <defs>
      <linearGradient id="rg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="var(--accent)" stop-opacity=".15" />
        <stop offset="100%" stop-color="#4f46e5" stop-opacity=".05" />
      </linearGradient>
      <filter id="gl"><feGaussianBlur stdDeviation="2"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <polygon v-if="pts" :points="pts" fill="url(#rg)" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round" filter="url(#gl)" />
    <template v-if="dims.length">
      <circle v-for="(d,i) in dims" :key="'p'+i" :cx="(d.score/100*76)*Math.cos(a(i))" :cy="(d.score/100*76)*Math.sin(a(i))" r="4" fill="var(--accent)" stroke="var(--surface)" stroke-width="2" />
      <text v-for="(d,i) in dims" :key="'s'+i" :x="(d.score/100*76+10)*Math.cos(a(i))" :y="(d.score/100*76+10)*Math.sin(a(i))" text-anchor="middle" dominant-baseline="middle" font-size="10" font-weight="700" fill="var(--text)">{{ d.score }}</text>
      <text v-for="(d,i) in dims" :key="'l'+i" :x="93*Math.cos(a(i))" :y="93*Math.sin(a(i))" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="var(--text2)">{{ d.name }}</text>
    </template>
  </svg>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ dimensions: Array })
const dims = computed(() => props.dimensions || [])
const pts = computed(() => dims.value.map((d, i) => { const r = d.score / 100 * 76; const ang = a(i); return `${r*Math.cos(ang)},${r*Math.sin(ang)}` }).join(' '))
function a(i) { return -Math.PI / 2 + 2 * Math.PI * (i || 0) / 5 }
</script>

<style scoped>
.radar { width: 170px; height: 170px; flex-shrink: 0; }
</style>
