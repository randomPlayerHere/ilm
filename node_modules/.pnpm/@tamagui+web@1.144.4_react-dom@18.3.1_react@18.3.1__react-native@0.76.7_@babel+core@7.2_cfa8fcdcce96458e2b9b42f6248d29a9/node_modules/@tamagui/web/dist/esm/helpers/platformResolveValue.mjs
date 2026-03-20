import { getTokenForKey } from "./getTokenForKey.mjs";
const tokenPattern = /(\$[\w.-]+)/g;
function platformResolveValue(_key, value, styleProps, styleState) {
  return value.replace(tokenPattern, t => {
    let r = getTokenForKey("size", t, styleProps, styleState);
    return r == null && (r = getTokenForKey("color", t, styleProps, styleState)), r != null ? String(r) : t;
  });
}
export { platformResolveValue };
//# sourceMappingURL=platformResolveValue.mjs.map
