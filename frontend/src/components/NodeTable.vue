<template>
  <div>
    <h2>Active Nodes</h2>
    <table>
      <tr>
        <th>Name</th>
        <th>IP</th>
        <th>CPU %</th>
        <th>Temp °C</th>
        <th>Status</th>
        <th>Last Seen</th>
      </tr>
      <tr v-for="node in nodes" :key="node.uid">
        <td>{{ node.name }}</td>
        <td>{{ node.ip }}</td>
        <td>{{ node.cpu }}</td>
        <td>{{ node.temp }}</td>
        <td>{{ node.status }}</td>
        <td>{{ node.last_seen }}</td>
      </tr>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return { nodes: [] }
  },
  mounted() {
    this.fetchNodes()
    setInterval(this.fetchNodes, 2000)  // refresh every 2s
  },
  methods: {
    async fetchNodes() {
      const res = await fetch("http://localhost:8000/api/nodes")
      this.nodes = await res.json()
    }
  }
}
</script>
