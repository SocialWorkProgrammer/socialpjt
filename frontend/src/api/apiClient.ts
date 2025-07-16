import axios from "axios";
import type { AxiosRequestConfig } from "axios";

const apiClient = axios.create({
  baseURL: "/api", // 필요에 따라 baseURL 수정
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청/응답 인터셉터 예시 (에러 핸들링 등)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 에러 공통 처리
    return Promise.reject(error);
  }
);

// CRUD 공통 함수
export const api = {
  get: <T = unknown>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then((res) => res.data),
  post: <T = unknown, D = unknown>(
    url: string,
    data?: D,
    config?: AxiosRequestConfig
  ) => apiClient.post<T>(url, data, config).then((res) => res.data),
  put: <T = unknown, D = unknown>(
    url: string,
    data?: D,
    config?: AxiosRequestConfig
  ) => apiClient.put<T>(url, data, config).then((res) => res.data),
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then((res) => res.data),
};

export default apiClient;
