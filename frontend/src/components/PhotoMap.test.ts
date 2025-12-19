import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount } from "@vue/test-utils";
import PhotoMap from "./PhotoMap.vue";

// Mock leaflet module
vi.mock("leaflet", () => ({
  default: {
    map: vi.fn(() => ({
      setView: vi.fn().mockReturnThis(),
      remove: vi.fn(),
    })),
    tileLayer: vi.fn(() => ({
      addTo: vi.fn(),
    })),
    marker: vi.fn(() => ({
      addTo: vi.fn().mockReturnThis(),
      bindPopup: vi.fn(),
      setLatLng: vi.fn(),
    })),
  },
}));

// Mock leaflet CSS import
vi.mock("leaflet/dist/leaflet.css", () => ({}));

describe("PhotoMap", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without errors", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 37.7749,
        longitude: -122.4194,
      },
    });

    expect(wrapper.exists()).toBe(true);
  });

  it("renders map container", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 37.7749,
        longitude: -122.4194,
      },
    });

    expect(wrapper.find(".photo-map-container").exists()).toBe(true);
    expect(wrapper.find(".map").exists()).toBe(true);
  });

  it("accepts latitude and longitude props", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 51.5074,
        longitude: -0.1278,
      },
    });

    expect(wrapper.props("latitude")).toBe(51.5074);
    expect(wrapper.props("longitude")).toBe(-0.1278);
  });

  it("accepts optional photoTitle prop", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 40.7128,
        longitude: -74.006,
        photoTitle: "New York Photo",
      },
    });

    expect(wrapper.props("photoTitle")).toBe("New York Photo");
  });

  it("uses default zoom level when not provided", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 48.8566,
        longitude: 2.3522,
      },
    });

    expect(wrapper.props("zoom")).toBe(13);
  });

  it("accepts custom zoom level", () => {
    const wrapper = mount(PhotoMap, {
      props: {
        latitude: 48.8566,
        longitude: 2.3522,
        zoom: 15,
      },
    });

    expect(wrapper.props("zoom")).toBe(15);
  });
});
