<template>
  <div>
    <h2>Unified Log</h2>
    <div v-for="msg in logs" :key="msg.timestamp">{{ msg }}</div>
  </div>
</template>

<script>
export default {
  data() { return { logs: [] } },
  mounted() {
    this.fetchLogs()
    setInterval(this.fetchLogs, 2000)
  },
  methods: {
    async fetchLogs() {
      const res = await fetch("http://localhost:8000/api/logs")
      this.logs = await res.json()
    }
  }
}
</script>
