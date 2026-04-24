<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>分析结果</span>
        <el-button size="small" @click="load" :loading="loading">刷新</el-button>
      </div>
    </template>

    <el-table :data="rows" size="small" :loading="loading" height="640">
      <el-table-column prop="opinion_title" label="舆情标题" min-width="220" show-overflow-tooltip />
      <el-table-column label="谣言" width="110">
        <template #default="{ row }">
          {{ rumorLabelZh(row.rumor_label) }}
        </template>
      </el-table-column>
      <el-table-column label="谣言概率" width="110">
        <template #default="{ row }">
          {{ formatProb(row.rumor_probability) }}
        </template>
      </el-table-column>
      <el-table-column label="情感" width="90">
        <template #default="{ row }">
          {{ sentimentLabelZh(row.sentiment_label) }}
        </template>
      </el-table-column>
      <el-table-column label="情感概率" width="110">
        <template #default="{ row }">
          {{ formatProb(row.sentiment_probability) }}
        </template>
      </el-table-column>
      <el-table-column label="关键词" min-width="220">
        <template #default="{ row }">
          <span v-if="row.keywords?.length">
            <el-tag v-for="k in row.keywords" :key="k" size="small" style="margin-right: 6px">
              {{ k }}
            </el-tag>
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="model_name" label="模型" min-width="160" show-overflow-tooltip />
      <el-table-column label="分析时间" min-width="170">
        <template #default="{ row }">
          {{ formatYmdHm(row.analyzed_at) }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { listAnalysisResults } from "@/api/analysis";
import type { AnalysisResult } from "@/types/api";

const rows = ref<AnalysisResult[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    rows.value = await listAnalysisResults();
  } finally {
    loading.value = false;
  }
}

function rumorLabelZh(v: string) {
  if (v === "rumor") return "疑似谣言";
  if (v === "non_rumor") return "非谣言";
  return v || "-";
}

function sentimentLabelZh(v: string) {
  if (v === "positive") return "正向";
  if (v === "neutral") return "中性";
  if (v === "negative") return "负向";
  return v || "-";
}

function formatProb(v: number) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(2);
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

