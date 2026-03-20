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
var setupGestureHandler_exports = {};
__export(setupGestureHandler_exports, {
  isGestureHandlerEnabled: () => isGestureHandlerEnabled,
  setupGestureHandler: () => setupGestureHandler
});
module.exports = __toCommonJS(setupGestureHandler_exports);
var import_native = require("@tamagui/native");
function isGestureHandlerEnabled() {
  return (0, import_native.getGestureHandler)().isEnabled;
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
    Gesture && GestureDetector && (0, import_native.getGestureHandler)().set({
      enabled: !0,
      Gesture,
      GestureDetector,
      ScrollView: ScrollView || null
    });
  }
}
//# sourceMappingURL=setupGestureHandler.native.js.map
