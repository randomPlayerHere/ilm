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
var resolveRem_native_exports = {};
__export(resolveRem_native_exports, {
  isRemValue: () => isRemValue,
  resolveRem: () => resolveRem
});
module.exports = __toCommonJS(resolveRem_native_exports);
var import_react_native = require("react-native"),
  import_config = require("../config.native.js"),
  remRegex = /(-?[\d.]+)rem/g;
function resolveRem(value) {
  var _config_settings,
    config = (0, import_config.getConfig)(),
    _config_settings_remBaseFontSize,
    baseFontSize = (_config_settings_remBaseFontSize = config == null || (_config_settings = config.settings) === null || _config_settings === void 0 ? void 0 : _config_settings.remBaseFontSize) !== null && _config_settings_remBaseFontSize !== void 0 ? _config_settings_remBaseFontSize : 16;
  if (value.endsWith("rem") && !value.includes(" ")) {
    var numericValue = Number.parseFloat(value);
    if (!Number.isNaN(numericValue)) return import_react_native.PixelRatio.getFontScale() * baseFontSize * numericValue;
  }
  for (var result = 0, match; (match = remRegex.exec(value)) !== null;) {
    var numericValue1 = Number.parseFloat(match[1]);
    Number.isNaN(numericValue1) || (result += import_react_native.PixelRatio.getFontScale() * baseFontSize * numericValue1);
  }
  return remRegex.lastIndex = 0, result;
}
function isRemValue(value) {
  return typeof value == "string" && value.includes("rem");
}
//# sourceMappingURL=resolveRem.native.js.map
