<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>风险预警</span>
        <el-button size="small" @click="load" :loading="loading">刷新</el-button>
      </div>
    </template>

    <el-table :data="rows" size="small" :loading="loading" height="640">
      <el-table-column prop="opinion_title" label="舆情标题" min-width="220" show-overflow-tooltip />
      <el-table-column label="风险等级" width="110">
        <template #default="{ row }">
          <RiskLevelTag :level="row.risk_level" />
        </template>
      </el-table-column>
      <el-table-column label="风险得分" width="110">
        <template #default="{ row }">
          {{ formatScore(row.risk_score) }}
        </template>
      </el-table-column>
      <el-table-column prop="warning_reason" label="预警原因" min-width="260" show-overflow-tooltip />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          {{ statusZh(row.status) }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="170">
        <template #default="{ row }">
          {{ formatYmdHm(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { listWarnings } from "@/api/warnings";
import RiskLevelTag from "@/components/RiskLevelTag.vue";
import type { RiskWarning } from "@/types/api";

const rows = ref<RiskWarning[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    rows.value = await listWarnings();
  } finally {
    loading.value = false;
  }
}

function formatScore(v: number) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(2);
}

function statusZh(v: string) {
  if (v === "open") return "待处理";
  if (v === "processing") return "处理中";
  if (v === "closed") return "已处理";
  return v || "-";
}

function formatYmdHm(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso || "-";
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

load();
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
}
</style>

