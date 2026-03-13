import { ApiError, type ApiOptions } from "../types/http";

const API_BASE = "";

function toQueryString(query?: ApiOptions["query"]) {
  if (!query) {
    return "";
  }

  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });

  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

function buildHeaders(headers?: HeadersInit): Headers {
  const merged = new Headers(headers);

  if (!merged.has("Accept")) {
    merged.set("Accept", "application/json");
  }
  if (!merged.has("X-Requested-With")) {
    merged.set("X-Requested-With", "XMLHttpRequest");
  }

  return merged;
}

function getCookie(name: string) {
  const match = new RegExp(`(^|; )${name}=([^;]*)`).exec(document.cookie);
  if (!match) {
    return null;
  }

  return decodeURIComponent(match[2]);
}

function attachCsrfToken(headers?: HeadersInit): Headers {
  const merged = buildHeaders(headers);
  const token = getCookie("csrftoken");

  if (token && !merged.has("X-CSRFToken")) {
    merged.set("X-CSRFToken", token);
  }

  return merged;
}

export async function requestJson<T>(
  path: string,
  options: ApiOptions & RequestInit = {},
): Promise<T> {
  const { query, headers, ...init } = options;
  const method = ((init.method || "GET") as string).toUpperCase();
  const isUnsafeMethod = method !== "GET" && method !== "HEAD";
  const url = `${API_BASE}${path}${toQueryString(query)}`;

  const response = await fetch(url, {
    credentials: "include",
    redirect: "manual",
    ...init,
    headers: isUnsafeMethod ? attachCsrfToken(headers) : buildHeaders(headers),
  });

  if (response.status === 401) {
    let message = "로그인이 필요합니다.";
    let payload = undefined;
    try {
      payload = await response.json();
      message = (payload as { error?: { message?: string } })?.error?.message ?? message;
    } catch {
      // no-op
    }
    throw new ApiError(message, response.status, "authentication_required", payload);
  }

  if (
    response.status === 302 ||
    response.status === 303 ||
    response.status === 307 ||
    response.status === 308
  ) {
    const location = response.headers.get("Location") || "";
    throw new ApiError("리다이렉트가 감지되었습니다.", response.status, "redirect", {
      location,
    });
  }

  if (!response.ok) {
    let payload = undefined;
    try {
      payload = await response.json();
    } catch {
      payload = await response.text();
    }
    throw new ApiError("요청에 실패했습니다.", response.status, `http_${response.status}`, payload);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as unknown as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

export const apiClient = {
  get: <T>(path: string, query?: ApiOptions["query"], init: ApiOptions = {}) =>
    requestJson<T>(path, { ...init, method: "GET", query }),
  post: <T>(path: string, body?: unknown, init: ApiOptions = {}) => {
    const payload = body === undefined ? undefined : JSON.stringify(body);
    return requestJson<T>(path, {
      ...init,
      method: "POST",
      headers: {
        ...(init.headers || {}),
        "Content-Type": "application/json",
      },
      body: payload,
    });
  },
  postForm: <T>(
    path: string,
    form: Record<string, string>,
    init: ApiOptions = {},
  ) =>
    requestJson<T>(path, {
      ...init,
      method: "POST",
      headers: {
        ...(init.headers || {}),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(form).toString(),
    }),
  put: <T>(path: string, body?: unknown, init: ApiOptions = {}) =>
    requestJson<T>(path, {
      ...init,
      method: "PUT",
      headers: {
        ...(init.headers || {}),
        "Content-Type": "application/json",
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  delete: <T>(path: string, init: ApiOptions = {}) =>
    requestJson<T>(path, {
      ...init,
      method: "DELETE",
    }),
};
