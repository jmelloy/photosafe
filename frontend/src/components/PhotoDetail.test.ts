import { describe, it, expect, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import PhotoDetail from "./PhotoDetail.vue";
import type { Photo } from "../types/api";

describe("PhotoDetail", () => {
  const mockPhoto: Photo = {
    uuid: "test-uuid",
    original_filename: "test.jpg",
    date: "2025-12-15T14:03:35",
    file_size: 1024000,
    width: 5712,
    height: 4284,
    url: "https://example.com/test.jpg",
    favorite: false,
    hidden: false,
    isphoto: true,
    ismovie: false,
    burst: false,
    live_photo: false,
    portrait: false,
    screenshot: false,
    slow_mo: false,
    time_lapse: false,
    hdr: false,
    selfie: false,
    panorama: false,
    exif: {
      Flash: 16,
      FNumber: 1.78,
      LensMake: "Apple",
      LensModel: "iPhone 16 Pro back triple camera 6.765mm f/1.78",
      DateTimeOriginal: "2025:12:15 14:03:35",
      DateTimeDigitized: "2025:12:15 14:03:35",
      DateTime: "2025:12:15 14:03:35",
      ExposureTime: 0.00047393364928909954,
      ISOSpeedRatings: [80],
      FocalLength: 6.765,
      LensSpecification: [
        [4, 2.22],
        [4, 15.66],
        [4, 1.78],
        [4, 2.8],
      ],
      WhiteBalance: 0,
      ExposureProgram: 2,
      MeteringMode: 5,
      ExposureBiasValue: 0.0,
      BrightnessValue: 8.88,
      ColorSpace: 65535,
    },
  };

  beforeEach(() => {
    // Reset any mocks if needed
  });

  it("renders without errors", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    expect(wrapper.exists()).toBe(true);
  });

  it("displays photo filename", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    expect(wrapper.text()).toContain("test.jpg");
  });

  it("formats date fields correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // Check that the date is formatted and not shown as "2025:12:15 14:03:35"
    expect(wrapper.text()).not.toContain("2025:12:15 14:03:35");
    expect(wrapper.text()).toContain("December 15, 2025");
  });

  it("formats LensSpecification correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // Check that LensSpecification is formatted as a readable string
    expect(wrapper.text()).toContain("2.2-15.7mm, f/1.8-2.8");
  });

  it("displays important EXIF fields", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    const text = wrapper.text();

    // Check important fields are displayed
    expect(text).toContain("Aperture");
    expect(text).toContain("f/1.8");
    expect(text).toContain("ISO");
    expect(text).toContain("Flash");
    expect(text).toContain("Lens Model");
  });

  it("has collapsible additional EXIF data section", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    const details = wrapper.find("details.exif-details");
    expect(details.exists()).toBe(true);

    const summary = details.find("summary");
    expect(summary.exists()).toBe(true);
    expect(summary.text()).toContain("Additional EXIF Data");
  });

  it("formats shutter speed correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // ExposureTime: 0.00047393364928909954 should become "1/2110s" or similar
    expect(wrapper.text()).toMatch(/1\/\d+s/);
  });

  it("formats flash values correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // Flash: 16 should be "Off, Did not fire"
    expect(wrapper.text()).toContain("Off, Did not fire");
  });

  it("formats white balance correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // WhiteBalance: 0 should be "Auto"
    expect(wrapper.text()).toContain("Auto");
  });

  it("formats exposure program correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // ExposureProgram: 2 should be "Normal program"
    expect(wrapper.text()).toContain("Normal program");
  });

  it("formats metering mode correctly", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: mockPhoto,
      },
    });

    // MeteringMode: 5 should be "Pattern"
    expect(wrapper.text()).toContain("Pattern");
  });

  it("does not show EXIF section when exif is empty", () => {
    const photoWithoutExif: Photo = {
      ...mockPhoto,
      exif: {},
    };

    const wrapper = mount(PhotoDetail, {
      props: {
        photo: photoWithoutExif,
      },
    });

    expect(wrapper.text()).not.toContain("EXIF Data");
  });

  it("handles missing photo prop", () => {
    const wrapper = mount(PhotoDetail, {
      props: {
        photo: null,
      },
    });

    // Should not crash and render nothing
    expect(wrapper.html()).toBe("<!--v-if-->");
  });
});
