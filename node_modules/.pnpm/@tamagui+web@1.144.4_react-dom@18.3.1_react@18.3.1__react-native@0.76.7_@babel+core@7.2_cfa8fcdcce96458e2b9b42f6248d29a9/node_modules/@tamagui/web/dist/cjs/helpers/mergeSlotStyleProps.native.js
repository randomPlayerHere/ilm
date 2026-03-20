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
var mergeSlotStyleProps_exports = {};
__export(mergeSlotStyleProps_exports, {
  mergeSlotStyleProps: () => mergeSlotStyleProps
});
module.exports = __toCommonJS(mergeSlotStyleProps_exports);
var import_compose_refs = require("@tamagui/compose-refs"),
  import_helpers = require("@tamagui/helpers"),
  isEventHandler = /^on[A-Z]/;
function mergeSlotStyleProps(base, overlay) {
  for (var key in overlay) {
    var baseVal = base[key],
      overlayVal = overlay[key];
    overlayVal !== void 0 && (key === "style" ? base.style = baseVal && overlayVal ? {
      ...baseVal,
      ...overlayVal
    } : overlayVal || baseVal : key === "className" ? base.className = baseVal && overlayVal ? `${baseVal} ${overlayVal}` : overlayVal || baseVal : key === "ref" ? base.ref = baseVal && overlayVal ? (0, import_compose_refs.composeRefs)(baseVal, overlayVal) : overlayVal || baseVal : isEventHandler.test(key) && typeof baseVal == "function" && typeof overlayVal == "function" ? base[key] = (0, import_helpers.composeEventHandlers)(baseVal, overlayVal) : base[key] = overlayVal);
  }
  return base;
}
//# sourceMappingURL=mergeSlotStyleProps.native.js.map
