<template>
  <el-tag :type="tagType" effect="light" size="small">
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RiskLevel } from "@/types/api";

const props = defineProps<{ level: RiskLevel }>();

const tagType = computed(() => {
  if (props.level === "high") return "danger";
  if (props.level === "medium") return "warning";
  return "success";
});

const label = computed(() => {
  if (props.level === "high") return "高风险";
  if (props.level === "medium") return "中风险";
  return "低风险";
});
</script>

