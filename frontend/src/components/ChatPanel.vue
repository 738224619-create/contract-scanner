<template>
  <div class="chat">
    <div class="chat-msgs" ref="msgs">
      <div v-if="messages.length === 0" class="empty">有问题直接问 AI</div>
      <div v-for="(m,i) in messages" :key="i" :class="['msg', m.role]">
        <span class="avatar">{{ m.role === 'user' ? '你' : 'AI' }}</span>
        <div class="bubble">{{ m.text }}</div>
      </div>
      <div v-if="loading" class="msg assistant"><span class="avatar">AI</span><div class="bubble typing">···</div></div>
    </div>
    <form class="form" @submit.prevent="send">
      <input v-model="q" placeholder="追问…" :disabled="loading" />
      <button type="submit" :disabled="!q.trim() || loading">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 2l12 6-12 6 3-6-3-6z" fill="currentColor"/></svg>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
const props = defineProps({ aid: Number, visible: Boolean })
const messages = ref([]); const q = ref(''); const loading = ref(false); const msgs = ref(null)
async function send() {
  const t = q.value.trim(); if (!t) return
  messages.value.push({ role: 'user', text: t }); q.value = ''; loading.value = true
  try { messages.value.push({ role: 'assistant', text: (await (await fetch(`/api/chat/${props.aid}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ question:t }) })).json()).answer }) }
  catch { messages.value.push({ role: 'assistant', text: '回答失败' }) }
  finally { loading.value = false; nextTick(() => msgs.value && (msgs.value.scrollTop = msgs.value.scrollHeight)) }
}
</script>

<style scoped>
.chat { margin-top: 28px; padding-top: 24px; border-top: 1px solid var(--border); }
.chat-msgs { max-height: 300px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 14px; }
.empty { text-align: center; color: var(--text3); font-size: 14px; padding: 12px 0; }
.msg { display: flex; gap: 10px; align-items: flex-start; max-width: 85%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.avatar { font-size: 12px; font-weight: 600; color: var(--text2); flex-shrink: 0; padding-top: 5px; width: 20px; }
.bubble { padding: 10px 16px; border-radius: 16px; font-size: 14px; line-height: 1.55; }
.msg.user .bubble { background: var(--accent); color: #fff; }
.msg.assistant .bubble { background: var(--surface2); color: var(--text); }
.typing { animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:.25} 50%{opacity:1} }
.form { display: flex; gap: 8px; }
.form input { flex: 1; padding: 12px 18px; background: var(--surface2); border: 1px solid var(--border); border-radius: 14px; font-size: 14px; color: var(--text); outline: none; transition: border-color .2s; }
.form input:focus { border-color: var(--accent); }
.form input::placeholder { color: var(--text3); }
.form button { width: 44px; height: 44px; background: var(--accent); color: #fff; border: none; border-radius: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background .2s; flex-shrink: 0; }
.form button:hover { background: #8b6cf6; }
.form button:disabled { opacity: .3; cursor: not-allowed; }
</style>
