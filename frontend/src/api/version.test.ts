import { describe, it, expect, vi, beforeEach } from "vitest";
import { getVersion } from "./version";
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
      const mockVersion = { version: "1.0.15" };
      vi.mocked(api.get).mockResolvedValue({ data: mockVersion } as any);

      const result = await getVersion();

      expect(api.get).toHaveBeenCalledWith("/version");
      expect(result).toEqual(mockVersion);
    });

    it("should return version object with version string", async () => {
      const mockVersion = { version: "2.3.4" };
      vi.mocked(api.get).mockResolvedValue({ data: mockVersion } as any);

      const result = await getVersion();

      expect(result).toHaveProperty("version");
      expect(typeof result.version).toBe("string");
    });
  });
});
