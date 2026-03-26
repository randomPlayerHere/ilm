import { analyzeImageQuality } from "../useImageQuality";
import * as ImageManipulator from "expo-image-manipulator";

jest.mock("expo-image-manipulator", () => ({
  manipulateAsync: jest.fn(),
  SaveFormat: { JPEG: "jpeg" },
}));

describe("analyzeImageQuality", () => {
  const mockManipulateAsync = ImageManipulator.manipulateAsync as jest.MockedFunction<
    typeof ImageManipulator.manipulateAsync
  >;

  it("returns isBlurry: false when compression takes normal time", async () => {
    // Simulate normal compression time (> 50ms)
    mockManipulateAsync.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({ uri: "file://thumb.jpg", width: 100, height: 100, base64: undefined }),
            60
          )
        )
    );
    const result = await analyzeImageQuality("file://photo.jpg");
    expect(result.isBlurry).toBe(false);
  });

  it("returns isBlurry: true when compression is suspiciously fast", async () => {
    // Simulate instant (blank/blurry image) compression
    mockManipulateAsync.mockResolvedValue({
      uri: "file://thumb.jpg",
      width: 100,
      height: 100,
      base64: undefined,
    });
    const result = await analyzeImageQuality("file://blank.jpg");
    expect(result.isBlurry).toBe(true);
  });

  it("returns isBlurry: false (safe default) if manipulateAsync throws", async () => {
    mockManipulateAsync.mockRejectedValue(new Error("Native error"));
    const result = await analyzeImageQuality("file://bad.jpg");
    expect(result.isBlurry).toBe(false);
  });

  it("returns safe default if quality analysis times out", async () => {
    jest.useFakeTimers();
    try {
      mockManipulateAsync.mockImplementation(() => new Promise(() => {}));
      const resultPromise = analyzeImageQuality("file://slow.jpg");
      jest.advanceTimersByTime(901);
      const result = await resultPromise;
      expect(result.isBlurry).toBe(false);
      expect(result.reason).toBe("Quality check timed out");
    } finally {
      jest.useRealTimers();
    }
  });
});
