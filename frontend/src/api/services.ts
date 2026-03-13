import { apiClient } from "./http";

export type SocialServiceItem = {
  id: number;
  source: string;
  source_label: string;
  title: string;
  summary: string;
  detail_url: string;
  region_ctpv: string;
  region_sgg: string;
  target_names: string;
  theme_names: string;
  life_names: string;
  apply_method_name: string;
  support_type: string;
  online_applicable: boolean | null;
  view_count: number | null;
  external_id: string;
  site_url: string;
  fetched_at: string | null;
};

export type PaginationState = {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_previous: boolean;
  has_next: boolean;
};

export type ServiceListResponse = {
  ok: boolean;
  items: SocialServiceItem[];
  pagination: PaginationState;
};

export type ServiceDetailResponse = {
  ok: boolean;
  item: SocialServiceItem;
};

export type RecommendationPayload = {
  age_group?: string;
  region_ctpv?: string;
  region_sgg?: string;
  target_type?: string;
  life_stage?: string;
  interest_theme?: string;
  special_notes?: string;
};

export type RecommendationResponse = {
  profile: Record<string, string>;
  recommendations: Array<{
    service_id: number;
    source: string;
    title: string;
    score: number;
    region: string;
    target: string;
    url: string;
  }>;
  llm: {
    provider: string;
    used_fallback: boolean;
    message: string;
  };
  blocked_fields?: string[];
  disclaimer: string;
};

export async function getServices(query: {
  q?: string;
  source?: string;
  category?: string;
  region?: string;
  page?: number;
  page_size?: number;
}) {
  return apiClient.get<ServiceListResponse>("/services/api/", query);
}

export async function getService(serviceId: string | number) {
  return apiClient.get<ServiceDetailResponse>(`/services/api/${serviceId}/`);
}

export async function getRecommendation(payload: RecommendationPayload) {
  return apiClient.post<RecommendationResponse>("/services/recommend/", payload);
}
