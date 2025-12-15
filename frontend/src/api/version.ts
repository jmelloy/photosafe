import api from "./client";

export interface VersionResponse {
  version: string;
  git_sha: string;
}

export const getVersion = async (): Promise<VersionResponse> => {
  const response = await api.get<VersionResponse>("/version");
  return response.data;
};

export const getClientGitSha = (): string => {
  return __GIT_SHA__;
};
