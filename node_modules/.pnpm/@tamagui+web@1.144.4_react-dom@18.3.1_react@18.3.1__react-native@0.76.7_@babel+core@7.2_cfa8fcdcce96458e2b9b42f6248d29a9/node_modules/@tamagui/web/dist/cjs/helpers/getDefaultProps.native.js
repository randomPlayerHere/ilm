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
var getDefaultProps_exports = {};
__export(getDefaultProps_exports, {
  getDefaultProps: () => getDefaultProps
});
module.exports = __toCommonJS(getDefaultProps_exports);
var import_config = require("../config.native.js"),
  getDefaultProps = function (staticConfig, propsComponentName) {
    var _conf_defaultProps,
      defaultProps = staticConfig?.defaultProps,
      conf = (0, import_config.getConfig)(),
      name = propsComponentName || staticConfig?.componentName || (
      // important: this is how we end up getting the defaultProps we set in createTamagui
      staticConfig.isText ? "Text" : "View"),
      userDefaultProps = conf == null || (_conf_defaultProps = conf.defaultProps) === null || _conf_defaultProps === void 0 ? void 0 : _conf_defaultProps[name];
    return userDefaultProps && (defaultProps = defaultProps ? {
      ...userDefaultProps,
      ...defaultProps
    } : userDefaultProps), defaultProps;
  };
//# sourceMappingURL=getDefaultProps.native.js.map
