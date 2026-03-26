import { compressImage } from "../image-compressor";
import * as ImageManipulator from "expo-image-manipulator";
import { Image } from "react-native";

jest.mock("expo-image-manipulator", () => ({
  manipulateAsync: jest.fn(),
  SaveFormat: { JPEG: "jpeg" },
}));

describe("compressImage", () => {
  const mockManipulateAsync = ImageManipulator.manipulateAsync as jest.MockedFunction<
    typeof ImageManipulator.manipulateAsync
  >;
  let mockGetSize: jest.SpiedFunction<typeof Image.getSize>;

  beforeAll(() => {
    mockGetSize = jest.spyOn(Image, "getSize");
  });

  afterAll(() => {
    mockGetSize.mockRestore();
  });

  beforeEach(() => {
    mockGetSize.mockImplementation((_, success) => success(2560, 1440));
    mockManipulateAsync.mockResolvedValue({
      uri: "file://compressed.jpg",
      width: 1920,
      height: 1080,
      base64: undefined,
    });
  });

  it("resizes landscape images by width and applies compress params", async () => {
    await compressImage("file://original.jpg");
    expect(mockManipulateAsync).toHaveBeenCalledWith(
      "file://original.jpg",
      [{ resize: { width: 1920 } }],
      { compress: 0.75, format: "jpeg" }
    );
  });

  it("resizes portrait images by height", async () => {
    mockGetSize.mockImplementation((_, success) => success(1200, 3000));

    await compressImage("file://portrait.jpg");
    expect(mockManipulateAsync).toHaveBeenCalledWith(
      "file://portrait.jpg",
      [{ resize: { height: 1920 } }],
      { compress: 0.75, format: "jpeg" }
    );
  });

  it("does not upscale images that are already within max dimension", async () => {
    mockGetSize.mockImplementation((_, success) => success(800, 600));

    await compressImage("file://small.jpg");
    expect(mockManipulateAsync).toHaveBeenCalledWith(
      "file://small.jpg",
      [],
      { compress: 0.75, format: "jpeg" }
    );
  });

  it("returns the compressed URI and dimensions", async () => {
    const result = await compressImage("file://original.jpg");
    expect(result.uri).toBe("file://compressed.jpg");
    expect(result.width).toBe(1920);
    expect(result.height).toBe(1080);
  });

  it("uses knownSize to skip Image.getSize when provided", async () => {
    mockGetSize.mockClear();
    await compressImage("file://original.jpg", { width: 3840, height: 2160 });
    expect(mockGetSize).not.toHaveBeenCalled();
    expect(mockManipulateAsync).toHaveBeenCalledWith(
      "file://original.jpg",
      [{ resize: { width: 1920 } }],
      { compress: 0.75, format: "jpeg" }
    );
  });
});
