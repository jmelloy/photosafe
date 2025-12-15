import { describe, it, expect, vi, beforeEach } from "vitest";
import { getVersion, getClientGitSha } from "./version";
import api from "./client";

// Mock the api client
vi.mock("./client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("Version API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getVersion", () => {
    it("should fetch version from the API", async () => {
      const mockVersion = { version: "1.0.15", git_sha: "abc123" };
      vi.mocked(api.get).mockResolvedValue({ data: mockVersion } as any);

      const result = await getVersion();

      expect(api.get).toHaveBeenCalledWith("/version");
      expect(result).toEqual(mockVersion);
    });

    it("should return version object with version string and git_sha", async () => {
      const mockVersion = { version: "2.3.4", git_sha: "def456" };
      vi.mocked(api.get).mockResolvedValue({ data: mockVersion } as any);

      const result = await getVersion();

      expect(result).toHaveProperty("version");
      expect(typeof result.version).toBe("string");
      expect(result).toHaveProperty("git_sha");
      expect(typeof result.git_sha).toBe("string");
    });
  });

  describe("getClientGitSha", () => {
    it("should return the client git sha", () => {
      const result = getClientGitSha();
      
      expect(typeof result).toBe("string");
      expect(result.length).toBeGreaterThan(0);
    });
  });
});
