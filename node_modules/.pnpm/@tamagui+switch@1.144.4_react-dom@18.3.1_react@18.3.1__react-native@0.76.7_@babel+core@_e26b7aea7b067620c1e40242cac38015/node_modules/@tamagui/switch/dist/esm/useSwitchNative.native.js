import { jsx as _jsx } from "react/jsx-runtime";
import { shouldRenderNativePlatform } from "@tamagui/core";
import { registerFocusable } from "@tamagui/focusable";
import * as React from "react";
import { Switch as NativeSwitch } from "react-native";
function useSwitchNative(props) {
  var {
    id,
    disabled,
    native,
    nativeProps,
    checked,
    setChecked
  } = props;
  React.useEffect(function () {
    if (id && !disabled) return registerFocusable(id, {
      focusAndSelect: function () {
        setChecked(function (value) {
          return !value;
        });
      },
      focus: function () {}
    });
  }, [id, disabled, setChecked]);
  var renderNative = shouldRenderNativePlatform(native);
  return renderNative === "android" || renderNative === "ios" ? /* @__PURE__ */_jsx(NativeSwitch, {
    value: checked,
    onValueChange: setChecked,
    ...nativeProps
  }) : null;
}
export { useSwitchNative };
//# sourceMappingURL=useSwitchNative.native.js.map
