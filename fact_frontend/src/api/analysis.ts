import { request } from "./request";
import type { AnalysisResult } from "@/types/api";

export async function listAnalysisResults() {
  const resp = await request.get<AnalysisResult[]>("/api/analysis/");
  return resp.data;
}

