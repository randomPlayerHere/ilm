import React from "react";
const getIcon = (el, props) => el && (React.isValidElement(el) ? React.cloneElement(el, {
  ...props,
  // @ts-expect-error
  ...el.props
}) : React.createElement(el, props));
export { getIcon };
//# sourceMappingURL=getIcon.mjs.map
