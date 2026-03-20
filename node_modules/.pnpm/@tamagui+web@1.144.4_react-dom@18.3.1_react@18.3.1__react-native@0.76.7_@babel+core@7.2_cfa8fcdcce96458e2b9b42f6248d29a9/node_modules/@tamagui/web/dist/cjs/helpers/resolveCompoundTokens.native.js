"use strict";

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
var resolveCompoundTokens_exports = {};
__export(resolveCompoundTokens_exports, {
  resolveCompoundTokens: () => resolveCompoundTokens
});
module.exports = __toCommonJS(resolveCompoundTokens_exports);
var import_platformResolveValue = require("./platformResolveValue.native.js"),
  compoundKeys = {
    boxShadow: !0,
    textShadow: !0,
    filter: !0,
    backgroundImage: !0,
    border: !0,
    outline: !0
  };
function resolveCompoundTokens(key, value, styleProps, styleState) {
  return !value.includes("$") || !compoundKeys[key] ? value : (0, import_platformResolveValue.platformResolveValue)(key, value, styleProps, styleState);
}
//# sourceMappingURL=resolveCompoundTokens.native.js.map
