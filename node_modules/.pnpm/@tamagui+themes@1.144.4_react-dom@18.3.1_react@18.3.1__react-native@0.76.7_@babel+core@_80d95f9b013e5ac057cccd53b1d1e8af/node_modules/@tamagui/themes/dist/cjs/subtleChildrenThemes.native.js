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
var subtleChildrenThemes_exports = {};
__export(subtleChildrenThemes_exports, {
  subtleChildrenThemes: () => subtleChildrenThemes,
  v5SubtlePaletteAdjustments: () => v5SubtlePaletteAdjustments
});
module.exports = __toCommonJS(subtleChildrenThemes_exports);
var import_v5_themes = require("./v5-themes.native.js"),
  v5SubtlePaletteAdjustments = {
    default: {
      light: function (hsl) {
        return {
          ...hsl,
          s: hsl.s * 0.9
        };
      },
      dark: function (hsl, i) {
        return {
          ...hsl,
          s: hsl.s * (i <= 4 ? 0.7 : 0.9)
        };
      }
    },
    // yellow palette in radix is especially off from the rest
    yellow: {
      light: function (hsl, i) {
        var t = (i - 1) / 11,
          sStart = 0.65,
          sEnd = 0.4,
          lStart = 1.08,
          lEnd = 0.8;
        return {
          ...hsl,
          s: hsl.s * (sStart + t * (sEnd - sStart)),
          l: hsl.l * (lStart + t * (lEnd - lStart))
        };
      },
      dark: function (hsl, i) {
        return {
          ...hsl,
          s: hsl.s * (i <= 7 ? 0.45 : 0.55),
          l: hsl.l * (i <= 4 ? 0.8 : 1)
        };
      }
    }
  },
  subtleChildrenThemes = (0, import_v5_themes.adjustPalettes)(import_v5_themes.defaultChildrenThemes, {
    ...v5SubtlePaletteAdjustments,
    gray: void 0,
    // skip
    neutral: void 0
  });
//# sourceMappingURL=subtleChildrenThemes.native.js.map
