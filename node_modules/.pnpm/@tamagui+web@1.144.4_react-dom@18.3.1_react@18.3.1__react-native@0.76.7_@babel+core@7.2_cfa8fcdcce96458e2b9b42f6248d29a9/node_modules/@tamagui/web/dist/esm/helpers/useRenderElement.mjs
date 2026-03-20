import { cloneElement, createElement, isValidElement } from "react";
import { composeRefs } from "@tamagui/compose-refs";
import { mergeSlotStyleProps } from "./mergeSlotStyleProps.mjs";
function evaluateRenderProp(render, props, state, defaultElement) {
  if (!render) return defaultElement;
  const defaultChildren = defaultElement.props.children;
  if (typeof render == "string") return createElement(render, props, defaultChildren);
  if (typeof render == "function") return render(props, state);
  if (isValidElement(render)) {
    const renderProps = render.props,
      renderRef = renderProps?.ref;
    if (!renderProps || Object.keys(renderProps).length === 0) return renderRef ? cloneElement(render, {
      ...props,
      ref: composeRefs(props.ref, renderRef)
    }, defaultChildren) : cloneElement(render, props, defaultChildren);
    const merged = mergeSlotStyleProps({
        ...props
      }, renderProps),
      children = renderProps.children ?? defaultChildren;
    return cloneElement(render, merged, children);
  }
  return defaultElement;
}
export { evaluateRenderProp };
//# sourceMappingURL=useRenderElement.mjs.map
