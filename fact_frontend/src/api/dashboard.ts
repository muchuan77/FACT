import { request } from "./request";
import type { DashboardSummary } from "@/types/api";

export async function getDashboardSummary() {
  const resp = await request.get<DashboardSummary>("/api/dashboard/summary/");
  return resp.data;
}

