import { apiClient } from "./http";

export type NewsItem = {
  news_id: number;
  title: string;
  content: string;
  source_url: string;
  created_at: string;
  fetched_at: string;
};

export type PaginationState = {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_previous: boolean;
  has_next: boolean;
};

export type NewsListResponse = {
  ok: boolean;
  items: NewsItem[];
  pagination: PaginationState;
};

export type NewsDetailResponse = {
  ok: boolean;
  item: NewsItem;
};

export async function getNewsList(query: { q?: string; page?: number; page_size?: number }) {
  return apiClient.get<NewsListResponse>("/news/api/", query);
}

export async function getNewsDetail(newsId: string | number) {
  return apiClient.get<NewsDetailResponse>(`/news/api/${newsId}/`);
}
