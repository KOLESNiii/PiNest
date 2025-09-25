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
        <td style="display: flex; align-items: center; justify-content: space-between;">
          <span>{{ node.name }}</span>
          <span 
            style="cursor: pointer; color: blue;" 
            @click="editNodeName(node)">
            ✏️
          </span>
        </td>
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
    setInterval(this.fetchNodes, 500)  // refresh every 2s
  },
  methods: {
    async fetchNodes() {
      const res = await fetch("http://localhost:8000/api/nodes")
      this.nodes = await res.json()
    },
    async editNodeName(node) {
      const newName = prompt("Enter new name for node:", node.name)
      if (newName && newName !== node.name) {
        try {
          const res = await fetch("http://localhost:8000/api/rename", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid: node.uid, name: newName })
          })
          const data = await res.json()
          if (!data.error) {
            node.name = data.new_name  // update locally
            alert(`Node renamed: ${data.old_name} → ${data.new_name}`)
          } else {
            alert("Error: " + data.error)
          }
        } catch (err) {
          alert("Failed to rename node: " + err)
        }
      }
    }
  }
}
</script>
