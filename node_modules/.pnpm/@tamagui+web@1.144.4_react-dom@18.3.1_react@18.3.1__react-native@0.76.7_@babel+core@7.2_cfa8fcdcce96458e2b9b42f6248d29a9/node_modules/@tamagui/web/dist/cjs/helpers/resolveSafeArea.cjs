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
var resolveSafeArea_exports = {};
__export(resolveSafeArea_exports, {
  resolveSafeAreaValue: () => resolveSafeAreaValue
});
module.exports = __toCommonJS(resolveSafeArea_exports);
const safeAreaTokens = {
  $safeAreaTop: "env(safe-area-inset-top)",
  $safeAreaBottom: "env(safe-area-inset-bottom)",
  $safeAreaLeft: "env(safe-area-inset-left)",
  $safeAreaRight: "env(safe-area-inset-right)"
};
function resolveSafeAreaValue(value) {
  return safeAreaTokens[value];
}