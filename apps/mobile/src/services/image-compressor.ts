import * as ImageManipulator from "expo-image-manipulator";
import { Image } from "react-native";

export interface CompressedImage {
  uri: string;
  width: number;
  height: number;
}

const MAX_DIMENSION = 1920; // ~2MP when both sides ≤ 1920
const JPEG_QUALITY = 0.75;

function getImageSize(uri: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    Image.getSize(
      uri,
      (width, height) => resolve({ width, height }),
      reject,
    );
  });
}

/**
 * Compress an image to ~2MP resolution at JPEG quality 0.75.
 * Preserves aspect ratio by constraining the longest side to MAX_DIMENSION.
 * Safe to call multiple times (idempotent for already-compressed images).
 *
 * Pass knownSize when the caller already has image dimensions (e.g. from
 * takePictureAsync) to avoid a redundant Image.getSize I/O round-trip.
 */
export async function compressImage(
  uri: string,
  knownSize?: { width: number; height: number }
): Promise<CompressedImage> {
  const { width, height } = knownSize ?? await getImageSize(uri);
  const longestSide = Math.max(width, height);

  const actions: ImageManipulator.Action[] = [];
  if (longestSide > MAX_DIMENSION) {
    if (width >= height) {
      actions.push({ resize: { width: MAX_DIMENSION } });
    } else {
      actions.push({ resize: { height: MAX_DIMENSION } });
    }
  }

  const result = await ImageManipulator.manipulateAsync(
    uri,
    actions,
    {
      compress: JPEG_QUALITY,
      format: ImageManipulator.SaveFormat.JPEG,
    }
  );
  return {
    uri: result.uri,
    width: result.width,
    height: result.height,
  };
}
