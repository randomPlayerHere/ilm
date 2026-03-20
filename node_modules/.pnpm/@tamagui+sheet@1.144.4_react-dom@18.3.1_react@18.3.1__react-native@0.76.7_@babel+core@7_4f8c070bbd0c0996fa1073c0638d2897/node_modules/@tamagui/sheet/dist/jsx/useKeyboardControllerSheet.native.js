"use strict";

var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
    for (var name in all) __defProp(target, name, {
      get: all[name],
      enumerable: !0
    });
  },
  __copyProps = (to, from, except, desc) => {
    if (from && typeof from == "object" || typeof from == "function") for (let key of __getOwnPropNames(from)) !__hasOwnProp.call(to, key) && key !== except && __defProp(to, key, {
      get: () => from[key],
      enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
    });
    return to;
  };
var __toCommonJS = mod => __copyProps(__defProp({}, "__esModule", {
  value: !0
}), mod);
var useKeyboardControllerSheet_native_exports = {};
__export(useKeyboardControllerSheet_native_exports, {
  useKeyboardControllerSheet: () => useKeyboardControllerSheet
});
module.exports = __toCommonJS(useKeyboardControllerSheet_native_exports);
var import_react = require("react"),
  import_react_native = require("react-native"),
  isKeyboardControllerEnabled = function () {
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
    [keyboardHeight, setKeyboardHeight] = (0, import_react.useState)(0),
    [isKeyboardVisible, setIsKeyboardVisible] = (0, import_react.useState)(!1),
    keyboardControllerEnabled = isKeyboardControllerEnabled(),
    pauseKeyboardHandler = (0, import_react.useRef)(!1),
    pendingHide = (0, import_react.useRef)(!1),
    dismissKeyboard = (0, import_react.useCallback)(function () {
      if (import_react_native.Keyboard.dismiss(), keyboardControllerEnabled) try {
        var _KeyboardController_dismiss,
          {
            KeyboardController
          } = getKeyboardControllerState();
        KeyboardController == null || (_KeyboardController_dismiss = KeyboardController.dismiss) === null || _KeyboardController_dismiss === void 0 || _KeyboardController_dismiss.call(KeyboardController);
      } catch {}
    },
    // ignore errors from keyboard-controller
    [keyboardControllerEnabled]),
    flushPendingHide = (0, import_react.useCallback)(function () {
      pendingHide.current && (pendingHide.current = !1, setIsKeyboardVisible(!1), setKeyboardHeight(0));
    }, []);
  return (0, import_react.useEffect)(function () {
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
  }, [enabled, keyboardControllerEnabled]), (0, import_react.useEffect)(function () {
    if (enabled && !keyboardControllerEnabled) {
      var showEvent = import_react_native.Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow",
        hideEvent = import_react_native.Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide",
        showListener = import_react_native.Keyboard.addListener(showEvent, function (e) {
          setKeyboardHeight(e.endCoordinates.height), setIsKeyboardVisible(!0);
        }),
        hideListener = import_react_native.Keyboard.addListener(hideEvent, function () {
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
//# sourceMappingURL=useKeyboardControllerSheet.native.js.map
