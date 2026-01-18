import api from "./client";

export interface AppleCredential {
  id: number;
  user_id: number;
  apple_id: string;
  is_active: boolean;
  requires_2fa: boolean;
  created_at: string;
  updated_at: string;
  last_authenticated_at: string | null;
}

export interface AppleCredentialCreate {
  apple_id: string;
  password: string;
}

export interface AppleAuthSession {
  id: number;
  credential_id: number;
  is_authenticated: boolean;
  requires_2fa: boolean;
  awaiting_2fa_code: boolean;
  trusted_devices: any[] | null;
  session_token: string | null;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

export interface AppleAuth2FARequest {
  session_token: string;
  code: string;
}

export interface AppleAuth2FAResponse {
  success: boolean;
  message: string;
  session: AppleAuthSession | null;
}

/**
 * Create or update Apple/iCloud credentials
 */
export const createAppleCredential = async (
  data: AppleCredentialCreate
): Promise<AppleCredential> => {
  const response = await api.post<AppleCredential>("/apple/credentials", data);
  return response.data;
};

/**
 * List all Apple/iCloud credentials for the current user
 */
export const listAppleCredentials = async (): Promise<AppleCredential[]> => {
  const response = await api.get<AppleCredential[]>("/apple/credentials");
  return response.data;
};

/**
 * Get a specific Apple/iCloud credential
 */
export const getAppleCredential = async (
  credentialId: number
): Promise<AppleCredential> => {
  const response = await api.get<AppleCredential>(
    `/apple/credentials/${credentialId}`
  );
  return response.data;
};

/**
 * Delete an Apple/iCloud credential
 */
export const deleteAppleCredential = async (
  credentialId: number
): Promise<void> => {
  await api.delete(`/apple/credentials/${credentialId}`);
};

/**
 * Initiate Apple/iCloud authentication
 */
export const initiateAppleAuth = async (
  credentialId: number
): Promise<AppleAuthSession> => {
  const response = await api.post<AppleAuthSession>("/apple/auth/initiate", {
    credential_id: credentialId,
  });
  return response.data;
};

/**
 * Submit 2FA code for authentication
 */
export const submit2FACode = async (
  request: AppleAuth2FARequest
): Promise<AppleAuth2FAResponse> => {
  const response = await api.post<AppleAuth2FAResponse>(
    "/apple/auth/2fa",
    request
  );
  return response.data;
};

/**
 * Get the status of an authentication session
 */
export const getAuthSession = async (
  sessionToken: string
): Promise<AppleAuthSession> => {
  const response = await api.get<AppleAuthSession>(
    `/apple/auth/session/${sessionToken}`
  );
  return response.data;
};
