import { mergeSlotStyleProps } from "./mergeSlotStyleProps.native.js";
function mergeRenderElementProps(elementProps, viewProps, children) {
  var merged = mergeSlotStyleProps({
    ...elementProps
  }, viewProps);
  return merged.children = children, merged;
}
export { mergeRenderElementProps };
//# sourceMappingURL=mergeRenderElementProps.native.js.map
