import React from "react";
var getIcon = function (el, props) {
  return el && (/* @__PURE__ */React.isValidElement(el) ? /* @__PURE__ */React.cloneElement(el, {
    ...props,
    // @ts-expect-error
    ...el.props
  }) : /* @__PURE__ */React.createElement(el, props));
};
export { getIcon };
//# sourceMappingURL=getIcon.native.js.map
