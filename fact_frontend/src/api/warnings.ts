import { request } from "./request";
import type { RiskWarning } from "@/types/api";

export async function listWarnings() {
  const resp = await request.get<RiskWarning[]>("/api/warnings/");
  return resp.data;
}
