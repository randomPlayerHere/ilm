import * as ImageManipulator from "expo-image-manipulator";

export interface ImageQualityResult {
  isBlurry: boolean;
  reason?: string;
}

const THUMBNAIL_SIZE = 100;
const FAST_COMPRESS_THRESHOLD_MS = 50; // Images that compress this fast are likely low-detail
const ANALYSIS_TIMEOUT_MS = 900;

/**
 * Heuristic blur check: resize to thumbnail and time the operation.
 * Returns { isBlurry: true } if the image appears to be blank or very low detail.
 * This is advisory — always < 1s. The teacher can override with "Use Anyway".
 */
export async function analyzeImageQuality(uri: string): Promise<ImageQualityResult> {
  const start = Date.now();
  let timeoutHandle: ReturnType<typeof setTimeout> | null = null;
  try {
    const qualityPromise = ImageManipulator.manipulateAsync(
      uri,
      [{ resize: { width: THUMBNAIL_SIZE, height: THUMBNAIL_SIZE } }],
      { compress: 0.5, format: ImageManipulator.SaveFormat.JPEG }
    );

    const timeoutPromise = new Promise<"timeout">((resolve) => {
      timeoutHandle = setTimeout(() => resolve("timeout"), ANALYSIS_TIMEOUT_MS);
    });

    const qualityResult = await Promise.race([qualityPromise, timeoutPromise]);

    if (qualityResult === "timeout") {
      return { isBlurry: false, reason: "Quality check timed out" };
    }

    if (timeoutHandle) {
      clearTimeout(timeoutHandle);
      timeoutHandle = null;
    }

    const elapsed = Date.now() - start;
    if (elapsed < FAST_COMPRESS_THRESHOLD_MS) {
      return {
        isBlurry: true,
        reason: "Photo may be blurry or blank",
      };
    }
    return { isBlurry: false };
  } catch {
    if (timeoutHandle) {
      clearTimeout(timeoutHandle);
    }
    // If analysis fails, don't block the flow
    return { isBlurry: false };
  }
}
