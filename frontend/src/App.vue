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
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>IP</th>
              <th>CPU %</th>
              <th>Temp °C</th>
              <th>Status</th>
              <th>Last Seen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="node in nodes" :key="node.uid">
              <td>{{ node.name }}</td>
              <td>{{ node.ip }}</td>
              <td>{{ node.cpu }}</td>
              <td>{{ node.temp }}</td>
              <td :class="node.status">{{ node.status }}</td>
              <td>{{ node.last_seen }}</td>
            </tr>
          </tbody>
        </table>
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
            <tr v-for="(log, index) in logs" :key="index">
              <td>{{ log.timestamp || '-' }}</td>
              <td>{{ log.origin || 'Unknown' }}</td>
              <td :class="['level-' + (log.level || 'I').toUpperCase()]">
                {{ log.level || 'I' }}
              </td>
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

export default {
  name: "App",
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
    setInterval(this.fetchNodes, 2000);
    setInterval(this.fetchLogs, 2000);
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
  },
};
</script>
