import { platformResolveValue } from "./platformResolveValue.mjs";
const compoundKeys = {
  boxShadow: !0,
  textShadow: !0,
  filter: !0,
  backgroundImage: !0,
  border: !0,
  outline: !0
};
function resolveCompoundTokens(key, value, styleProps, styleState) {
  return !value.includes("$") || !compoundKeys[key] ? value : platformResolveValue(key, value, styleProps, styleState);
}
export { resolveCompoundTokens };
//# sourceMappingURL=resolveCompoundTokens.mjs.map
