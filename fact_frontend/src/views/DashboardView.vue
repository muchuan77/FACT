<template>
  <el-row :gutter="12">
    <el-col :xs="12" :sm="6">
      <StatCard title="舆情总数" :value="summary?.total_opinions ?? '-'" />
    </el-col>
    <el-col :xs="12" :sm="6">
      <StatCard title="已分析" :value="summary?.analyzed_count ?? '-'" />
    </el-col>
    <el-col :xs="12" :sm="6">
      <StatCard title="预警数量" :value="summary?.warning_count ?? '-'" />
    </el-col>
    <el-col :xs="12" :sm="6">
      <StatCard title="高风险" :value="summary?.high_risk_count ?? '-'" />
    </el-col>
  </el-row>

  <el-row :gutter="12" style="margin-top: 12px">
    <el-col :span="16">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">统计概览</div>
        </template>
        <div ref="chartEl" class="chart" />
      </el-card>
    </el-col>
    <el-col :span="8">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">最近预警</div>
        </template>
        <el-table :data="summary?.latest_warnings ?? []" size="small" height="280">
          <el-table-column prop="opinion_title" label="舆情" min-width="140" show-overflow-tooltip />
          <el-table-column label="等级" width="90">
            <template #default="{ row }">
              <RiskLevelTag :level="row.risk_level" />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>

  <el-row :gutter="12" style="margin-top: 12px">
    <el-col :span="24">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">最近舆情</div>
        </template>
        <el-table :data="summary?.latest_opinions ?? []" size="small">
          <el-table-column prop="title" label="标题" min-width="260" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="120" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="关键词" min-width="220">
            <template #default="{ row }">
              <span v-if="(row.display_keywords ?? row.keywords)?.length">
                <el-tag
                  v-for="k in row.display_keywords ?? row.keywords"
                  :key="k"
                  size="small"
                  style="margin-right: 6px"
                >
                  {{ k }}
                </el-tag>
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="170">
            <template #default="{ row }">
              {{ formatYmdHm(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

import { getDashboardSummary } from "@/api/dashboard";
import StatCard from "@/components/StatCard.vue";
import RiskLevelTag from "@/components/RiskLevelTag.vue";
import StatusTag from "@/components/StatusTag.vue";
import type { DashboardSummary } from "@/types/api";

const summary = ref<DashboardSummary | null>(null);
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

async function load() {
  summary.value = await getDashboardSummary();
  await nextTick();
  renderChart();
}

function renderChart() {
  if (!chartEl.value || !summary.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  chart.setOption({
    tooltip: {},
    xAxis: { type: "category", data: ["舆情", "分析", "预警", "高风险"] },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: [
          summary.value.total_opinions,
          summary.value.analyzed_count,
          summary.value.warning_count,
          summary.value.high_risk_count,
        ],
      },
    ],
  });
}

function formatYmdHm(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso || "-";
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

onMounted(() => {
  load();
  window.addEventListener("resize", () => chart?.resize());
});

onBeforeUnmount(() => {
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.chart {
  height: 280px;
}
.card-header {
  font-weight: 700;
}
</style>

