function getOppositeScheme(scheme) {
  return scheme === "dark" ? "light" : "dark";
}
const colorStyleKeys = {
  backgroundColor: !0,
  borderColor: !0,
  borderTopColor: !0,
  borderRightColor: !0,
  borderBottomColor: !0,
  borderLeftColor: !0,
  borderBlockColor: !0,
  borderBlockEndColor: !0,
  borderBlockStartColor: !0,
  color: !0,
  shadowColor: !0,
  textDecorationColor: !0,
  textShadowColor: !0,
  tintColor: !0,
  outlineColor: !0
};
function isColorStyleKey(key) {
  return colorStyleKeys[key] === !0;
}
function getDynamicVal({
  scheme,
  val,
  oppositeVal
}) {
  const oppositeScheme = getOppositeScheme(scheme);
  return {
    dynamic: {
      [scheme]: val,
      [oppositeScheme]: oppositeVal
    }
  };
}
function extractValueFromDynamic(val, scheme) {
  return val?.dynamic ? val.dynamic[scheme] : val;
}
export { extractValueFromDynamic, getDynamicVal, getOppositeScheme, isColorStyleKey };
//# sourceMappingURL=getDynamicVal.mjs.map
