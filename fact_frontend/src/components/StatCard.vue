<template>
  <el-card shadow="never" class="stat-card">
    <div class="stat-title">{{ title }}</div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="hint" class="stat-hint">{{ hint }}</div>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  value: string | number;
  hint?: string;
}>();
</script>

<style scoped>
.stat-card {
  border-radius: 12px;
}
.stat-title {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  margin-top: 6px;
}
.stat-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 6px;
}
</style>

