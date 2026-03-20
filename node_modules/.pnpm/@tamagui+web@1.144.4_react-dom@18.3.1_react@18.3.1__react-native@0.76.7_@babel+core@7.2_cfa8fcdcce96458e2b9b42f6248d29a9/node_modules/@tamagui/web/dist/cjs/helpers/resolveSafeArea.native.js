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
var resolveSafeArea_native_exports = {};
__export(resolveSafeArea_native_exports, {
  resolveSafeAreaValue: () => resolveSafeAreaValue
});
module.exports = __toCommonJS(resolveSafeArea_native_exports);
var safeAreaEdges = {
  $safeAreaTop: "top",
  $safeAreaBottom: "bottom",
  $safeAreaLeft: "left",
  $safeAreaRight: "right"
};
function resolveSafeAreaValue(value) {
  var edge = safeAreaEdges[value];
  if (edge) {
    var g = globalThis,
      state = g.__tamagui_native_safe_area_state__;
    return state?.enabled && state.initialMetrics ? state.initialMetrics.insets[edge] : 0;
  }
}
//# sourceMappingURL=resolveSafeArea.native.js.map
