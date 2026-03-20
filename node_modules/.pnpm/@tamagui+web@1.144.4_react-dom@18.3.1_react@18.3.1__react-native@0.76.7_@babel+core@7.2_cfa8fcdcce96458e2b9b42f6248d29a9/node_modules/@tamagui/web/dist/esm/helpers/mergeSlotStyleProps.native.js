import { composeRefs } from "@tamagui/compose-refs";
import { composeEventHandlers } from "@tamagui/helpers";
var isEventHandler = /^on[A-Z]/;
function mergeSlotStyleProps(base, overlay) {
  for (var key in overlay) {
    var baseVal = base[key],
      overlayVal = overlay[key];
    overlayVal !== void 0 && (key === "style" ? base.style = baseVal && overlayVal ? {
      ...baseVal,
      ...overlayVal
    } : overlayVal || baseVal : key === "className" ? base.className = baseVal && overlayVal ? `${baseVal} ${overlayVal}` : overlayVal || baseVal : key === "ref" ? base.ref = baseVal && overlayVal ? composeRefs(baseVal, overlayVal) : overlayVal || baseVal : isEventHandler.test(key) && typeof baseVal == "function" && typeof overlayVal == "function" ? base[key] = composeEventHandlers(baseVal, overlayVal) : base[key] = overlayVal);
  }
  return base;
}
export { mergeSlotStyleProps };
//# sourceMappingURL=mergeSlotStyleProps.native.js.map
