import { mergeSlotStyleProps } from "./mergeSlotStyleProps.mjs";
function mergeRenderElementProps(elementProps, viewProps, children) {
  const merged = mergeSlotStyleProps({
    ...elementProps
  }, viewProps);
  return merged.children = children, merged;
}
export { mergeRenderElementProps };
//# sourceMappingURL=mergeRenderElementProps.mjs.map
