import React from "react";
import { getConfig } from "../config.mjs";
import { Theme } from "./Theme.mjs";
import { jsx } from "react/jsx-runtime";
let defaultFontClass = "";
function TamaguiRoot({
  children,
  theme,
  isRootRoot,
  passThrough,
  style
}) {
  const [mounted, setMounted] = React.useState(!isRootRoot);
  if (React.useEffect(() => {
    mounted || setMounted(!0);
  }, []), !defaultFontClass) {
    const defaultFont = getConfig().defaultFont;
    defaultFont && (defaultFontClass = `font_${defaultFont}`);
  }
  const contents = /* @__PURE__ */jsx("span", {
    style,
    className: `_dsp_contents ${mounted ? "" : "t_unmounted"} ${defaultFontClass}`,
    children
  });
  return isRootRoot ? contents : /* @__PURE__ */jsx(Theme, {
    passThrough,
    contain: !0,
    forceClassName: !0,
    name: theme,
    children: contents
  });
}
export { TamaguiRoot };
//# sourceMappingURL=TamaguiRoot.mjs.map
