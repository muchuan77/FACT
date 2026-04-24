export type RiskLevel = "low" | "medium" | "high";

export interface OpinionData {
  id: number;
  title: string;
  content: string;
  source: string;
  source_url: string;
  publish_time: string | null;
  crawl_time: string | null;
  category: string;
  raw_label: string;
  keywords: string[];
  status: "new" | "analyzed" | "warned" | "closed";
  created_at: string;
  updated_at: string;
}

export interface AnalysisResult {
  id: number;
  opinion: number;
  opinion_title?: string;
  rumor_label: string;
  rumor_probability: number;
  sentiment_label: string;
  sentiment_probability: number;
  keywords: string[];
  model_name: string;
  analyzed_at: string;
}

export interface RiskWarning {
  id: number;
  opinion: number;
  opinion_title?: string;
  analysis_result: number | null;
  risk_score: number;
  risk_level: RiskLevel;
  warning_reason: string;
  status: string;
  created_at: string;
}

export interface DashboardSummary {
  total_opinions: number;
  analyzed_count: number;
  warning_count: number;
  high_risk_count: number;
  latest_opinions: Array<{
    id: number;
    title: string;
    source: string;
    status: string;
    keywords: string[];
    display_keywords?: string[];
    created_at: string;
  }>;
  latest_warnings: Array<{
    id: number;
    opinion_id: number;
    opinion_title: string;
    risk_level: RiskLevel;
    risk_score: number;
    status: string;
    created_at: string;
  }>;
}

export interface AnalyzeResponse {
  opinion: OpinionData;
  analysis_result: AnalysisResult;
  risk_warning: RiskWarning;
  note?: string;
}

