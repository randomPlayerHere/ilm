var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
    for (var name in all) __defProp(target, name, {
      get: all[name],
      enumerable: !0
    });
  },
  __copyProps = (to, from, except, desc) => {
    if (from && typeof from == "object" || typeof from == "function") for (let key of __getOwnPropNames(from)) !__hasOwnProp.call(to, key) && key !== except && __defProp(to, key, {
      get: () => from[key],
      enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
    });
    return to;
  };
var __toCommonJS = mod => __copyProps(__defProp({}, "__esModule", {
  value: !0
}), mod);
var getDynamicVal_exports = {};
__export(getDynamicVal_exports, {
  extractValueFromDynamic: () => extractValueFromDynamic,
  getDynamicVal: () => getDynamicVal,
  getOppositeScheme: () => getOppositeScheme,
  isColorStyleKey: () => isColorStyleKey
});
module.exports = __toCommonJS(getDynamicVal_exports);
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