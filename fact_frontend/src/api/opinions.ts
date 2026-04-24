import { request } from "./request";
import type { AnalyzeResponse, OpinionData } from "@/types/api";

export async function listOpinions() {
  const resp = await request.get<OpinionData[]>("/api/opinions/");
  return resp.data;
}

export async function createOpinion(payload: Partial<OpinionData>) {
  const resp = await request.post<OpinionData>("/api/opinions/", payload);
  return resp.data;
}

export async function getOpinionDetail(id: number) {
  const resp = await request.get<OpinionData>(`/api/opinions/${id}/`);
  return resp.data;
}

export async function analyzeOpinion(id: number) {
  const resp = await request.post<AnalyzeResponse>(`/api/opinions/${id}/analyze/`, {});
  return resp.data;
}

