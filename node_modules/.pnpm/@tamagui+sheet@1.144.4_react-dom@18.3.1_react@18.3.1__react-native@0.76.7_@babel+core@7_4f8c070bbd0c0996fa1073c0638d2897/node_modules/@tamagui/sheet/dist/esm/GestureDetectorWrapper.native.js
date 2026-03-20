import { jsx as _jsx } from "react/jsx-runtime";
import { View } from "react-native";
import { getGestureHandlerState, isGestureHandlerEnabled } from "./gestureState.native.js";
function GestureDetectorWrapper(param) {
  var {
      gesture,
      children,
      style
    } = param,
    {
      GestureDetector
    } = getGestureHandlerState(),
    enabled = isGestureHandlerEnabled();
  return enabled && GestureDetector && gesture ? /* @__PURE__ */_jsx(GestureDetector, {
    gesture,
    children: /* @__PURE__ */_jsx(View, {
      style,
      collapsable: !1,
      children
    })
  }) : /* @__PURE__ */_jsx(View, {
    style,
    children
  });
}
export { GestureDetectorWrapper };
//# sourceMappingURL=GestureDetectorWrapper.native.js.map
