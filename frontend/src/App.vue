<template>
  <div id="app">
    <h1>PiNest Dashboard</h1>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'nodes' }" @click="currentTab='nodes'">Nodes</button>
      <button :class="{ active: currentTab === 'logs' }" @click="currentTab='logs'">Logs</button>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <!-- Nodes Tab -->
      <div v-if="currentTab === 'nodes'">
        <NodeTable :nodes="nodes" @rename="handleRename" />
      </div>

      <!-- Logs Tab -->
      <div v-if="currentTab === 'logs'" class="logs">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Origin</th>
              <th>Level</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, index) in logs" :key="index" :class="(log.level || 'I').toUpperCase()">
              <td>{{ log.timestamp || '-' }}</td>
              <td>{{ log.origin || 'Unknown' }}</td>
              <td>{{ log.level || 'I' }}</td>
              <td>{{ log.message || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import './assets/style.css';
import NodeTable from './components/NodeTable.vue';

export default {
  name: "App",
  components: { NodeTable },
  data() {
    return {
      currentTab: "nodes",
      nodes: [],
      logs: [],
    };
  },
  mounted() {
    this.fetchNodes();
    this.fetchLogs();

    // Refresh every 2 seconds
    setInterval(this.fetchNodes, 500);
    setInterval(this.fetchLogs, 500);
  },
  methods: {
    async fetchNodes() {
      try {
        const res = await fetch("http://localhost:8000/api/nodes");
        this.nodes = await res.json();
      } catch (err) {
        console.error("Failed to fetch nodes:", err);
      }
    },
    async fetchLogs() {
      try {
        const res = await fetch("http://localhost:8000/api/logs");
        const data = await res.json();
        this.logs = data;
      } catch (err) {
        console.error("Failed to fetch logs:", err);
      }
    },
    async handleRename({ uid, oldName, newName }) {
    try {
      const res = await fetch("http://localhost:8000/api/rename", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, name: newName })
      })
      const data = await res.json()
      if (data.error) {
        alert("Error: " + data.error)
      }
    } catch (err) {
      alert("Failed to rename node: " + err)
    }
  }
  },
};
</script>
