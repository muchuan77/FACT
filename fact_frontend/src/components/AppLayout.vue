<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">
        <div class="brand-title">FACT</div>
        <div class="brand-sub">舆情风险预警与谣言治理</div>
      </div>
      <el-menu :default-active="activePath" router>
        <el-menu-item index="/dashboard">Dashboard</el-menu-item>
        <el-menu-item index="/opinions">舆情</el-menu-item>
        <el-menu-item index="/analysis">分析结果</el-menu-item>
        <el-menu-item index="/warnings">风险预警</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">{{ pageTitle }}</div>
        <div class="header-right">
          <el-tag type="info" effect="plain" size="small">MVP</el-tag>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const activePath = computed(() => route.path);

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    "/dashboard": "数据概览",
    "/opinions": "舆情列表",
    "/analysis": "分析结果",
    "/warnings": "风险预警",
  };
  return map[route.path] ?? "FACT";
});
</script>

<style scoped>
.layout {
  min-height: 100vh;
  background: #f6f7fb;
}
.aside {
  background: #ffffff;
  border-right: 1px solid var(--el-border-color);
}
.brand {
  padding: 16px 14px;
  border-bottom: 1px solid var(--el-border-color);
}
.brand-title {
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0.5px;
}
.brand-sub {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid var(--el-border-color);
}
.header-left {
  font-weight: 700;
}
.main {
  padding: 16px;
}
</style>

