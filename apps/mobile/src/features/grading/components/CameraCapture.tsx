import { useRef, useState } from "react";
import { StyleSheet, View, Text, Pressable, ActivityIndicator } from "react-native";
import { CameraView, CameraType, FlashMode } from "expo-camera";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { colors, fonts, fontWeights } from "@ilm/design-tokens";
import { compressImage } from "../../../services/image-compressor";
import { analyzeImageQuality } from "../hooks/useImageQuality";
import { setPendingCapture } from "../pending-capture-store";

export interface CaptureResult {
  compressedUri: string;
  originalUri: string;
  width: number;
  height: number;
}

interface CameraCaptureProps {
  onCaptureAccepted: (result: CaptureResult) => void;
  onDismiss: () => void;
}

type CaptureState =
  | "idle"
  | "capturing"
  | "analyzing"
  | "blurry_warning"
  | "processing";

export function CameraCapture({ onCaptureAccepted, onDismiss }: CameraCaptureProps) {
  const cameraRef = useRef<CameraView | null>(null);
  const [facing] = useState<CameraType>("back");
  const [flash, setFlash] = useState<FlashMode>("off");
  const [captureState, setCaptureState] = useState<CaptureState>("idle");
  const [pendingCompressed, setPendingCompressedState] = useState<CaptureResult | null>(null);

  async function handleShutter() {
    if (!cameraRef.current || captureState !== "idle") return;
    setCaptureState("capturing");

    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 1 });
      if (!photo) { setCaptureState("idle"); return; }

      setCaptureState("analyzing");

      // Run quality check and compression in parallel.
      // Pass photo dimensions to compressImage to skip redundant Image.getSize lookup.
      const [qualityResult, compressed] = await Promise.all([
        analyzeImageQuality(photo.uri),
        compressImage(photo.uri, { width: photo.width, height: photo.height }),
      ]);

      const captureResult: CaptureResult = {
        compressedUri: compressed.uri,
        originalUri: photo.uri,
        width: compressed.width,
        height: compressed.height,
      };
      setPendingCompressedState(captureResult);

      if (qualityResult.isBlurry) {
        setCaptureState("blurry_warning");
      } else {
        acceptCapture(captureResult);
      }
    } catch {
      setCaptureState("idle");
    }
  }

  function acceptCapture(result: CaptureResult) {
    setCaptureState("processing");
    setPendingCapture({
      ...result,
      capturedAt: new Date().toISOString(),
    });
    onCaptureAccepted(result);
  }

  function handleRetake() {
    setCaptureState("idle");
    setPendingCompressedState(null);
  }

  function handleUseAnyway() {
    if (pendingCompressed) acceptCapture(pendingCompressed);
  }

  const isProcessing = captureState === "capturing" || captureState === "analyzing" || captureState === "processing";

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing={facing} flash={flash}>
        {/* Alignment guide overlay */}
        <View style={styles.overlay} pointerEvents="none">
          <View style={styles.guideFrame}>
            {/* Corner indicators */}
            <View style={[styles.corner, styles.cornerTL]} />
            <View style={[styles.corner, styles.cornerTR]} />
            <View style={[styles.corner, styles.cornerBL]} />
            <View style={[styles.corner, styles.cornerBR]} />
          </View>
          <Text style={styles.hintText} accessibilityLabel="Position assignment within frame">
            Position assignment within frame
          </Text>
        </View>

        {/* Top controls */}
        <View style={styles.topControls}>
          <Pressable
            onPress={onDismiss}
            accessibilityLabel="Close camera"
            accessibilityRole="button"
            style={styles.iconButton}
          >
            <MaterialCommunityIcons name="close" size={28} color={colors.textInverse} />
          </Pressable>
          <Pressable
            onPress={() => setFlash((f: FlashMode) => f === "off" ? "on" : "off")}
            accessibilityLabel={flash === "off" ? "Turn flash on" : "Turn flash off"}
            accessibilityRole="button"
            style={styles.iconButton}
          >
            <MaterialCommunityIcons
              name={flash === "off" ? "flash-off" : "flash"}
              size={28}
              color={colors.textInverse}
            />
          </Pressable>
        </View>

        {/* Bottom controls */}
        <View style={styles.bottomControls}>
          {isProcessing ? (
            <ActivityIndicator size="large" color={colors.textInverse} accessibilityLabel="Processing image" />
          ) : (
            <Pressable
              onPress={handleShutter}
              accessibilityLabel="Take photo"
              accessibilityRole="button"
              style={styles.shutterButton}
            >
              <View style={styles.shutterInner} />
            </Pressable>
          )}
        </View>

        {/* Blur warning overlay */}
        {captureState === "blurry_warning" && (
          <View style={styles.blurWarning}>
            <Text style={styles.blurWarningTitle}>Photo may be blurry</Text>
            <View style={styles.blurWarningButtons}>
              <Pressable
                onPress={handleRetake}
                accessibilityLabel="Retake photo"
                accessibilityRole="button"
                style={[styles.blurButton, styles.blurButtonRetake]}
              >
                <Text style={styles.blurButtonText}>Retake</Text>
              </Pressable>
              <Pressable
                onPress={handleUseAnyway}
                accessibilityLabel="Use photo anyway"
                accessibilityRole="button"
                style={[styles.blurButton, styles.blurButtonUse]}
              >
                <Text style={[styles.blurButtonText, styles.blurButtonUseText]}>Use Anyway</Text>
              </Pressable>
            </View>
          </View>
        )}
      </CameraView>
    </View>
  );
}

const GUIDE_COLOR = colors.textInverse;
const CORNER_SIZE = 24;
const CORNER_THICKNESS = 3;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.textPrimary },
  camera: { flex: 1 },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
  },
  guideFrame: {
    width: "85%",
    aspectRatio: 1.414, // A4 paper ratio
    borderColor: colors.border,
    borderWidth: 1,
    position: "relative",
  },
  corner: {
    position: "absolute",
    width: CORNER_SIZE,
    height: CORNER_SIZE,
    borderColor: GUIDE_COLOR,
  },
  cornerTL: { top: -CORNER_THICKNESS, left: -CORNER_THICKNESS, borderTopWidth: CORNER_THICKNESS, borderLeftWidth: CORNER_THICKNESS },
  cornerTR: { top: -CORNER_THICKNESS, right: -CORNER_THICKNESS, borderTopWidth: CORNER_THICKNESS, borderRightWidth: CORNER_THICKNESS },
  cornerBL: { bottom: -CORNER_THICKNESS, left: -CORNER_THICKNESS, borderBottomWidth: CORNER_THICKNESS, borderLeftWidth: CORNER_THICKNESS },
  cornerBR: { bottom: -CORNER_THICKNESS, right: -CORNER_THICKNESS, borderBottomWidth: CORNER_THICKNESS, borderRightWidth: CORNER_THICKNESS },
  hintText: {
    marginTop: 16,
    color: GUIDE_COLOR,
    opacity: 0.8,
    fontSize: 13,
    fontFamily: fonts.body,
    fontWeight: fontWeights.regular,
    textAlign: "center",
  },
  topControls: {
    position: "absolute",
    top: 56,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 20,
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  bottomControls: {
    position: "absolute",
    bottom: 48,
    left: 0,
    right: 0,
    alignItems: "center",
  },
  shutterButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 4,
    borderColor: colors.textInverse,
    alignItems: "center",
    justifyContent: "center",
  },
  shutterInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.textInverse,
  },
  blurWarning: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.textPrimary,
    padding: 24,
    paddingBottom: 48,
    alignItems: "center",
    gap: 16,
  },
  blurWarningTitle: {
    color: colors.textInverse,
    fontSize: 16,
    fontFamily: fonts.body,
    fontWeight: fontWeights.semibold,
  },
  blurWarningButtons: {
    flexDirection: "row",
    gap: 12,
    width: "100%",
  },
  blurButton: {
    flex: 1,
    height: 48,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  blurButtonRetake: {
    borderWidth: 1,
    borderColor: colors.textInverse,
  },
  blurButtonUse: {
    backgroundColor: colors.primary,
  },
  blurButtonText: {
    color: colors.textInverse,
    fontSize: 15,
    fontFamily: fonts.body,
    fontWeight: fontWeights.medium,
  },
  blurButtonUseText: {
    color: colors.textInverse,
  },
});
