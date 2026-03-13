export type ApiErrorInfo = {
  code?: string;
  message?: string;
  detail?: string;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly payload?: unknown;

  constructor(message: string, status: number, code: string, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.payload = payload;
  }
}

export type ApiOptions = Omit<RequestInit, "body" | "method" | "headers"> & {
  query?: Record<string, string | number | boolean | undefined | null>;
};
