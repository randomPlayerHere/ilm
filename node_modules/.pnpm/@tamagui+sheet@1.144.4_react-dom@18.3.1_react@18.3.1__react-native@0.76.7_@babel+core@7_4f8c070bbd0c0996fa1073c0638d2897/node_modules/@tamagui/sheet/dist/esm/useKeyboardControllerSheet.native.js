import { useCallback, useEffect, useRef, useState } from "react";
import { Keyboard, Platform } from "react-native";
var isKeyboardControllerEnabled = function () {
    return !1;
  },
  getKeyboardControllerState = function () {
    return {};
  };
try {
  var nativeModule = require("@tamagui/native");
  isKeyboardControllerEnabled = nativeModule.isKeyboardControllerEnabled, getKeyboardControllerState = nativeModule.getKeyboardControllerState;
} catch {}
function useKeyboardControllerSheet(options) {
  var {
      enabled
    } = options,
    [keyboardHeight, setKeyboardHeight] = useState(0),
    [isKeyboardVisible, setIsKeyboardVisible] = useState(!1),
    keyboardControllerEnabled = isKeyboardControllerEnabled(),
    pauseKeyboardHandler = useRef(!1),
    pendingHide = useRef(!1),
    dismissKeyboard = useCallback(function () {
      if (Keyboard.dismiss(), keyboardControllerEnabled) try {
        var _KeyboardController_dismiss,
          {
            KeyboardController
          } = getKeyboardControllerState();
        KeyboardController == null || (_KeyboardController_dismiss = KeyboardController.dismiss) === null || _KeyboardController_dismiss === void 0 || _KeyboardController_dismiss.call(KeyboardController);
      } catch {}
    },
    // ignore errors from keyboard-controller
    [keyboardControllerEnabled]),
    flushPendingHide = useCallback(function () {
      pendingHide.current && (pendingHide.current = !1, setIsKeyboardVisible(!1), setKeyboardHeight(0));
    }, []);
  return useEffect(function () {
    if (!(!enabled || !keyboardControllerEnabled)) {
      var {
        KeyboardEvents
      } = getKeyboardControllerState();
      if (KeyboardEvents?.addListener) {
        var showSub = KeyboardEvents.addListener("keyboardWillShow", function (e) {
            var _e_height,
              height = (_e_height = e?.height) !== null && _e_height !== void 0 ? _e_height : 0;
            height > 0 && setKeyboardHeight(height), setIsKeyboardVisible(!0);
          }),
          hideSub = KeyboardEvents.addListener("keyboardWillHide", function () {
            if (pauseKeyboardHandler.current) {
              pendingHide.current = !0;
              return;
            }
            setIsKeyboardVisible(!1), setKeyboardHeight(0);
          });
        return function () {
          var _showSub_remove, _hideSub_remove;
          showSub == null || (_showSub_remove = showSub.remove) === null || _showSub_remove === void 0 || _showSub_remove.call(showSub), hideSub == null || (_hideSub_remove = hideSub.remove) === null || _hideSub_remove === void 0 || _hideSub_remove.call(hideSub);
        };
      }
    }
  }, [enabled, keyboardControllerEnabled]), useEffect(function () {
    if (enabled && !keyboardControllerEnabled) {
      var showEvent = Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
        hideEvent = Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide",
        showListener = Keyboard.addListener(showEvent, function (e) {
          setKeyboardHeight(e.endCoordinates.height), setIsKeyboardVisible(!0);
        }),
        hideListener = Keyboard.addListener(hideEvent, function () {
          if (pauseKeyboardHandler.current) {
            pendingHide.current = !0;
            return;
          }
          setIsKeyboardVisible(!1), setKeyboardHeight(0);
        });
      return function () {
        showListener.remove(), hideListener.remove();
      };
    }
  }, [enabled, keyboardControllerEnabled]), {
    keyboardControllerEnabled,
    keyboardHeight,
    isKeyboardVisible,
    dismissKeyboard,
    pauseKeyboardHandler,
    flushPendingHide
  };
}
export { useKeyboardControllerSheet };
//# sourceMappingURL=useKeyboardControllerSheet.native.js.map
