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
  name: "NodeTable",
  props: {
    nodes: {
      type: Array,
      required: true
    }
  },
  methods: {
    async editNodeName(node) {
      const newName = prompt("Enter new name for node:", node.name)
      if (newName && newName !== node.name) {
        this.$emit('rename', { uid: node.uid, oldName: node.name, newName })
      }
    }
  }
}
</script>
