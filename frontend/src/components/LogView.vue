<template>
  <div class="logs">
    <h2>Logs</h2>
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
</template>

<script>
export default {
  name: "LogView",
  props: {
    logs: {
      type: Array,
      required: true
    }
  }
}
</script>