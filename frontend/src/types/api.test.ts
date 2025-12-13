import { describe, it, expect } from "vitest";
import type { Photo, Album, User, Library, Version } from "./api";

describe("API Type Definitions", () => {
  describe("Photo type", () => {
    it("should allow valid photo object", () => {
      const photo: Photo = {
        uuid: "123e4567-e89b-12d3-a456-426614174000",
        original_filename: "test.jpg",
        date: "2024-01-01T00:00:00Z",
        title: "Test Photo",
        keywords: ["test"],
        favorite: false,
        hidden: false,
      };

      expect(photo.uuid).toBe("123e4567-e89b-12d3-a456-426614174000");
      expect(photo.original_filename).toBe("test.jpg");
    });

    it("should allow optional fields to be undefined", () => {
      const photo: Photo = {
        uuid: "test-uuid",
        original_filename: "test.jpg",
        date: "2024-01-01",
      };

      expect(photo.description).toBeUndefined();
      expect(photo.title).toBeUndefined();
    });
  });

  describe("Album type", () => {
    it("should allow valid album object", () => {
      const album: Album = {
        uuid: "album-uuid",
        title: "My Album",
      };

      expect(album.uuid).toBe("album-uuid");
      expect(album.title).toBe("My Album");
    });
  });

  describe("User type", () => {
    it("should allow valid user object", () => {
      const user: User = {
        id: 1,
        username: "testuser",
        email: "test@example.com",
        is_active: true,
        is_superuser: false,
        date_joined: "2024-01-01T00:00:00Z",
      };

      expect(user.id).toBe(1);
      expect(user.username).toBe("testuser");
      expect(user.is_active).toBe(true);
    });
  });

  describe("Library type", () => {
    it("should allow valid library object", () => {
      const library: Library = {
        id: 1,
        name: "My Library",
        owner_id: 1,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      };

      expect(library.id).toBe(1);
      expect(library.name).toBe("My Library");
    });
  });

  describe("Version type", () => {
    it("should allow valid version object", () => {
      const version: Version = {
        id: 1,
        version: "thumbnail",
        s3_path: "photos/thumb.jpg",
        width: 150,
        height: 150,
      };

      expect(version.id).toBe(1);
      expect(version.version).toBe("thumbnail");
    });
  });
});
