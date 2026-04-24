import { createRouter, createWebHistory } from "vue-router";

import AnalysisView from "@/views/AnalysisView.vue";
import DashboardView from "@/views/DashboardView.vue";
import OpinionDetailView from "@/views/OpinionDetailView.vue";
import OpinionListView from "@/views/OpinionListView.vue";
import WarningView from "@/views/WarningView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: DashboardView },
    { path: "/opinions", name: "opinions", component: OpinionListView },
    { path: "/opinions/:id", name: "opinion-detail", component: OpinionDetailView, props: true },
    { path: "/analysis", name: "analysis", component: AnalysisView },
    { path: "/warnings", name: "warnings", component: WarningView },
  ],
});

