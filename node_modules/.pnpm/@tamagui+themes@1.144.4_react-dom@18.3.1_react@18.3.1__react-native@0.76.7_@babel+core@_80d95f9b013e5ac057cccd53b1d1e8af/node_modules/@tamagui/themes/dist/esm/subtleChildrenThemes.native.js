import { defaultChildrenThemes, adjustPalettes } from "./v5-themes.native.js";
var v5SubtlePaletteAdjustments = {
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
  subtleChildrenThemes = adjustPalettes(defaultChildrenThemes, {
    ...v5SubtlePaletteAdjustments,
    gray: void 0,
    // skip
    neutral: void 0
  });
export { subtleChildrenThemes, v5SubtlePaletteAdjustments };
//# sourceMappingURL=subtleChildrenThemes.native.js.map
