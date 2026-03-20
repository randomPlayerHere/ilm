import { getGestureHandler } from "@tamagui/native";
function isGestureHandlerEnabled() {
  return getGestureHandler().isEnabled;
}
function setupGestureHandler(config) {
  var g = globalThis;
  if (!g.__tamagui_sheet_gesture_handler_setup) {
    g.__tamagui_sheet_gesture_handler_setup = !0;
    var {
      Gesture,
      GestureDetector,
      ScrollView
    } = config;
    Gesture && GestureDetector && getGestureHandler().set({
      enabled: !0,
      Gesture,
      GestureDetector,
      ScrollView: ScrollView || null
    });
  }
}
export { isGestureHandlerEnabled, setupGestureHandler };
//# sourceMappingURL=setupGestureHandler.native.js.map
