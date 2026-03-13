import { apiClient } from "./http";

export type CommunityItem = {
  id: number;
  title: string;
  content: string;
  author_email: string;
  is_pinned: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
};

export type PaginationState = {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_previous: boolean;
  has_next: boolean;
};

export type CommunityListResponse = {
  ok: boolean;
  items: CommunityItem[];
  pagination: PaginationState;
};

export type CommunityDetailResponse = {
  ok: boolean;
  item: CommunityItem;
};

export async function getCommunityList(query: { q?: string; page?: number }) {
  return apiClient.get<CommunityListResponse>("/community/api/", query);
}

export async function getCommunityDetail(postId: string | number) {
  return apiClient.get<CommunityDetailResponse>(`/community/api/${postId}/`);
}
