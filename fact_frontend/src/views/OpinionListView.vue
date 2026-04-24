<template>
  <el-row :gutter="12">
    <el-col :span="10">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">新增舆情</div>
        </template>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
          <el-form-item label="标题" prop="title">
            <el-input v-model="form.title" placeholder="请输入标题" />
          </el-form-item>
          <el-form-item label="正文" prop="content">
            <el-input v-model="form.content" type="textarea" :rows="5" placeholder="请输入正文内容" />
          </el-form-item>
          <el-form-item label="来源" prop="source">
            <el-input v-model="form.source" placeholder="如：微博/新闻/论坛" />
          </el-form-item>
          <el-form-item label="原文链接" prop="source_url">
            <el-input v-model="form.source_url" placeholder="https://..." />
          </el-form-item>
          <el-form-item label="发布时间" prop="publish_time">
            <el-date-picker
              v-model="form.publish_time"
              type="datetime"
              placeholder="选择日期时间（可选）"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="主题类别" prop="category">
            <el-select v-model="form.category" placeholder="请选择（可选）" clearable style="width: 100%">
              <el-option label="公共安全" value="公共安全" />
              <el-option label="校园舆情" value="校园舆情" />
              <el-option label="社会民生" value="社会民生" />
              <el-option label="医疗健康" value="医疗健康" />
              <el-option label="经济金融" value="经济金融" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="原始标签" prop="raw_label">
            <el-tooltip
              content="原始标签表示数据进入系统前已有的人工或数据集标注，不等同于本系统模型识别结果。若来源数据没有标签，请选择未知标签。"
              placement="top"
            >
              <el-icon style="margin-right: 6px"><InfoFilled /></el-icon>
            </el-tooltip>
            <el-select v-model="form.raw_label" placeholder="请选择（可选）" clearable style="width: 100%">
              <el-option label="未知标签（需模型判断）" value="unknown" />
              <el-option label="已标注谣言" value="rumor" />
              <el-option label="已标注非谣言" value="non_rumor" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词" prop="keywords">
            <el-select
              v-model="form.keywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词并回车（最多 8 个）"
              style="width: 100%"
            />
            <div style="margin-top: 8px">
              <el-button size="small" @click="onExtractKeywords">自动提取关键词</el-button>
              <span class="kw-hint">将从标题+正文提取，并优先加入风险词（最多保留 8 个）。</span>
            </div>
          </el-form-item>
          <el-form-item label="自动分析">
            <el-switch v-model="form.auto_analyze" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="onCreate">提交</el-button>
            <el-button :disabled="creating" @click="onReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>舆情列表</span>
            <el-button size="small" style="margin-left: 8px" @click="load" :loading="loading">刷新</el-button>
          </div>
        </template>
        <el-table
          :data="opinions"
          size="small"
          @row-click="goDetail"
          height="520"
          :row-class-name="() => 'clickable-row'"
        >
          <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="110" />
          <el-table-column label="原文" width="110">
            <template #default="{ row }">
              <el-button v-if="row.source_url" size="small" text type="primary" @click.stop="openUrl(row.source_url)">
                查看原文
              </el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="关键词" min-width="220">
            <template #default="{ row }">
              <span v-if="row.keywords?.length">
                <el-tag v-for="k in row.keywords" :key="k" size="small" style="margin-right: 6px">{{ k }}</el-tag>
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button size="small" type="primary" :loading="analyzingId === row.id" @click.stop="onAnalyze(row.id)">
                {{ analyzeButtonText(row.status) }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="hint">提示：点击任意行可进入详情页。</div>
      </el-card>
    </el-col>
  </el-row>

  <el-dialog v-model="resultVisible" title="分析结果" width="720px">
    <div v-if="analyzeResult">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="舆情标题">{{ analyzeResult.opinion.title }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ analyzeResult.opinion.status }}</el-descriptions-item>
        <el-descriptions-item label="谣言标签">{{ analyzeResult.analysis_result.rumor_label }}</el-descriptions-item>
        <el-descriptions-item label="谣言概率">{{ analyzeResult.analysis_result.rumor_probability }}</el-descriptions-item>
        <el-descriptions-item label="情感标签">{{ analyzeResult.analysis_result.sentiment_label }}</el-descriptions-item>
        <el-descriptions-item label="情感概率">{{ analyzeResult.analysis_result.sentiment_probability }}</el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <RiskLevelTag :level="analyzeResult.risk_warning.risk_level" />
        </el-descriptions-item>
        <el-descriptions-item label="风险得分">{{ analyzeResult.risk_warning.risk_score }}</el-descriptions-item>
        <el-descriptions-item label="关键词" :span="2">
          <el-tag v-for="k in analyzeResult.analysis_result.keywords" :key="k" size="small" style="margin-right: 6px">
            {{ k }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <div v-if="analyzeResult.note" class="note">note: {{ analyzeResult.note }}</div>
    </div>
    <template #footer>
      <el-button @click="resultVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import { InfoFilled } from "@element-plus/icons-vue";

import { analyzeOpinion, createOpinion, listOpinions } from "@/api/opinions";
import RiskLevelTag from "@/components/RiskLevelTag.vue";
import StatusTag from "@/components/StatusTag.vue";
import type { AnalyzeResponse, OpinionData } from "@/types/api";

const router = useRouter();

const opinions = ref<OpinionData[]>([]);
const loading = ref(false);
const creating = ref(false);
const analyzingId = ref<number | null>(null);

const formRef = ref<FormInstance>();

const form = reactive({
  title: "",
  content: "",
  source: "",
  source_url: "",
  publish_time: "" as string | "",
  category: "",
  raw_label: "" as string | "",
  keywords: [] as string[],
  auto_analyze: true,
});

const rules: FormRules = {
  title: [{ required: true, message: "标题不能为空", trigger: "blur" }],
  content: [{ required: true, message: "正文不能为空", trigger: "blur" }],
  source: [{ required: true, message: "来源平台不能为空", trigger: "blur" }],
  source_url: [{ type: "url", message: "请输入合法的 URL（如 https://...）", trigger: "blur" }],
};

const resultVisible = ref(false);
const analyzeResult = ref<AnalyzeResponse | null>(null);

async function load() {
  loading.value = true;
  try {
    opinions.value = await listOpinions();
  } finally {
    loading.value = false;
  }
}

function onReset() {
  form.title = "";
  form.content = "";
  form.source = "";
  form.source_url = "";
  form.publish_time = "";
  form.category = "";
  form.raw_label = "";
  form.keywords = [];
  form.auto_analyze = true;
  formRef.value?.clearValidate();
}

function normalizeKeywords(input: string[]) {
  const cleaned = input
    .map((x) => String(x || "").trim())
    .filter((x) => x.length > 0);
  const uniq: string[] = [];
  for (const k of cleaned) {
    if (!uniq.includes(k)) uniq.push(k);
    if (uniq.length >= 8) break;
  }
  return uniq;
}

function extractKeywordsFromText(title: string, content: string) {
  const text = `${title}\n${content}`;
  const riskBank = [
    "网传",
    "爆料",
    "事故",
    "学校",
    "学生",
    "食品安全",
    "公共安全",
    "恐慌",
    "严重",
    "吸毒",
    "贩毒",
    "诈骗",
    "疫情",
    "地震",
    "火灾",
    "暴力",
  ];

  const picked: string[] = [];
  for (const w of riskBank) {
    if (text.includes(w)) picked.push(w);
  }

  // 抽取长度>=2的中文片段，并用 2-4 字滑窗生成“词片段”
  const chunks = text.match(/[\u4e00-\u9fa5]{2,}/g) || [];
  for (const c of chunks) {
    const maxLen = Math.min(4, c.length);
    for (let len = 2; len <= maxLen; len += 1) {
      for (let i = 0; i + len <= c.length; i += 1) {
        picked.push(c.slice(i, i + len));
      }
    }
  }

  return normalizeKeywords(picked);
}

function onExtractKeywords() {
  form.keywords = extractKeywordsFromText(form.title, form.content);
  ElMessage.success("已自动提取关键词");
}

async function onCreate() {
  const ok = await formRef.value?.validate().catch(() => false);
  if (!ok) return;
  creating.value = true;
  try {
    const created = await createOpinion({
      title: form.title,
      content: form.content,
      source: form.source,
      category: form.category,
      source_url: form.source_url,
      publish_time: form.publish_time || null,
      raw_label: form.raw_label,
      keywords: normalizeKeywords(form.keywords),
    });
    ElMessage.success("新增成功");
    onReset();
    if (form.auto_analyze) {
      analyzeResult.value = await analyzeOpinion(created.id);
      resultVisible.value = true;
      ElMessage.success("自动分析完成");
    }
    await load();
  } finally {
    creating.value = false;
  }
}

async function onAnalyze(id: number) {
  analyzingId.value = id;
  try {
    analyzeResult.value = await analyzeOpinion(id);
    resultVisible.value = true;
    await load();
  } finally {
    analyzingId.value = null;
  }
}

function goDetail(row: OpinionData) {
  router.push({ name: "opinion-detail", params: { id: row.id } });
}

function openUrl(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}

function analyzeButtonText(status: OpinionData["status"]) {
  // 后端 analyze 已做幂等：已分析/已预警再点属于“查看结果”
  if (status === "new") return "分析";
  if (status === "analyzed" || status === "warned") return "查看结果";
  return "分析";
}

function formatDateTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("zh-CN", { hour12: false });
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
.hint {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.note {
  margin-top: 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>

<style>
.clickable-row {
  cursor: pointer;
}
</style>

