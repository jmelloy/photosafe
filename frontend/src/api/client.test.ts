import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getToken, setToken, removeToken } from "./client";

describe("API Client Token Management", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    // Clean up after each test
    localStorage.clear();
  });

  describe("getToken", () => {
    it("should return null when no token is stored", () => {
      expect(getToken()).toBeNull();
    });

    it("should return the stored token", () => {
      const token = "test-token-123";
      localStorage.setItem("photosafe_auth_token", token);
      expect(getToken()).toBe(token);
    });
  });

  describe("setToken", () => {
    it("should store the token in localStorage", () => {
      const token = "new-token-456";
      setToken(token);
      expect(localStorage.getItem("photosafe_auth_token")).toBe(token);
    });

    it("should overwrite existing token", () => {
      setToken("old-token");
      setToken("new-token");
      expect(getToken()).toBe("new-token");
    });
  });

  describe("removeToken", () => {
    it("should remove the token from localStorage", () => {
      setToken("token-to-remove");
      expect(getToken()).not.toBeNull();

      removeToken();
      expect(getToken()).toBeNull();
    });

    it("should not throw error when no token exists", () => {
      expect(() => removeToken()).not.toThrow();
    });
  });
});
