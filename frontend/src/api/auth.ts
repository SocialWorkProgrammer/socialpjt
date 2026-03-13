import { ApiError } from "../types/http";
import { apiClient } from "./http";

export type AuthUser = {
  id: number;
  email: string;
};

type AuthPayload = {
  ok: boolean;
  user?: AuthUser;
  error?: string;
  fields?: Record<string, string[]>;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type SignupInput = {
  email: string;
  password1: string;
  password2: string;
};

function mapAuthError(message: string, payload: unknown) {
  const data = payload as AuthPayload | undefined;
  if (data?.fields) {
    return Object.values(data.fields).flat().join("\n") || message;
  }

  return data?.error || message;
}

function assertAuthResponse(payload: AuthPayload): AuthUser {
  if (payload.ok && payload.user) {
    return payload.user;
  }

  throw new Error(payload.error ?? "요청이 거절되었습니다.");
}

export async function getSession(): Promise<AuthUser> {
  const payload = await apiClient.get<AuthPayload>("/accounts/me/");
  if (payload && payload.ok && payload.user) {
    return payload.user;
  }

  throw new Error("로그인되지 않았습니다.");
}

export async function loginWithSession(input: LoginInput): Promise<AuthUser> {
  try {
    const payload = await apiClient.postForm<AuthPayload>(
      "/accounts/login/",
      {
        username: input.email,
        password: input.password,
      },
      {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      },
    );
    return assertAuthResponse(payload);
  } catch (error) {
    if (error instanceof ApiError && error.payload) {
      throw new Error(mapAuthError(error.message, error.payload));
    }
    throw error;
  }
}

export async function signupWithSession(input: SignupInput): Promise<AuthUser> {
  try {
    const payload = await apiClient.postForm<AuthPayload>(
      "/accounts/signup/",
      {
        email: input.email,
        password1: input.password1,
        password2: input.password2,
      },
      {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      },
    );
    return assertAuthResponse(payload);
  } catch (error) {
    if (error instanceof ApiError && error.payload) {
      throw new Error(mapAuthError(error.message, error.payload));
    }
    throw error;
  }
}

export async function logoutSession(): Promise<void> {
  await apiClient.post<AuthPayload>(
    "/accounts/logout/",
    {},
    {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    },
  );
}
