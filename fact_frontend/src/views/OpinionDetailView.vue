<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <el-button text @click="router.back()">返回</el-button>
        <span>舆情详情</span>
      </div>
    </template>

    <el-skeleton :loading="loading" animated>
      <template #default>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ opinion?.title }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ opinion?.source }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ opinion?.category }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ opinion?.status }}</el-descriptions-item>
          <el-descriptions-item label="关键词" :span="2">
            <span v-if="opinion?.keywords?.length">
              <el-tag v-for="k in opinion?.keywords" :key="k" size="small" style="margin-right: 6px">{{ k }}</el-tag>
            </span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ opinion?.created_at }}</el-descriptions-item>
          <el-descriptions-item label="原文链接" :span="2">
            <el-link v-if="opinion?.source_url" :href="opinion?.source_url" target="_blank">
              {{ opinion?.source_url }}
            </el-link>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="正文" :span="2">
            <div class="content">{{ opinion?.content }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-skeleton>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getOpinionDetail } from "@/api/opinions";
import type { OpinionData } from "@/types/api";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const opinion = ref<OpinionData | null>(null);

onMounted(async () => {
  const id = Number(route.params.id);
  if (!Number.isFinite(id)) return;
  loading.value = true;
  try {
    opinion.value = await getOpinionDetail(id);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}
.content {
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>

