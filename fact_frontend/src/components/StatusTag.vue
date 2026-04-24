<template>
  <el-tag :type="tagType" effect="light" size="small">
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from "vue";

type Status = "new" | "analyzed" | "warned" | "closed" | string;

const props = defineProps<{ status: Status }>();

const tagType = computed(() => {
  if (props.status === "new") return "info";
  if (props.status === "analyzed") return "success";
  if (props.status === "warned") return "danger";
  return "";
});

const label = computed(() => {
  if (props.status === "new") return "待分析";
  if (props.status === "analyzed") return "已分析";
  if (props.status === "warned") return "已预警";
  if (props.status === "closed") return "已关闭";
  return props.status;
});
</script>

