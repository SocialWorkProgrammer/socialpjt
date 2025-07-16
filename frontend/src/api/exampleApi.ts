import { api } from "./apiClient";

// 예시: GET /example
export const getExampleData = async <T = unknown>() => {
  const response = await api.get<T>("/example");
  return response;
};

// 예시: GET /examples
export const getExamples = <T = unknown>() => api.get<T>("/examples");

// 예시: POST /examples
export const createExample = <T = unknown, D = unknown>(data: D) =>
  api.post<T, D>("/examples", data);

// 예시: PUT /examples/:id
export const updateExample = <T = unknown, D = unknown>(id: string, data: D) =>
  api.put<T, D>(`/examples/${id}`, data);

// 예시: DELETE /examples/:id
export const deleteExample = <T = unknown>(id: string) =>
  api.delete<T>(`/examples/${id}`);
