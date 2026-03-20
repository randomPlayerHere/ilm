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
var native_portal_exports = {};
__export(native_portal_exports, {
  setupNativePortal: () => setupNativePortal
});
module.exports = __toCommonJS(native_portal_exports);
var _global__IS_FABRIC,
  IS_FABRIC = typeof global < "u" && !!((_global__IS_FABRIC = global._IS_FABRIC) !== null && _global__IS_FABRIC !== void 0 ? _global__IS_FABRIC : global.nativeFabricUIManager),
  setupNativePortal = function () {
    var g = globalThis;
    if (!g.__tamagui_portal_create) {
      if (IS_FABRIC) {
        try {
          var _mod_default,
            mod = require("react-native/Libraries/Renderer/shims/ReactFabric"),
            _mod_default_createPortal;
          g.__tamagui_portal_create = (_mod_default_createPortal = mod == null || (_mod_default = mod.default) === null || _mod_default === void 0 ? void 0 : _mod_default.createPortal) !== null && _mod_default_createPortal !== void 0 ? _mod_default_createPortal : mod.createPortal;
        } catch (err) {
          console.info("Note: error importing fabric portal, native portals disabled", err);
        }
        return;
      }
      try {
        var _mod_default1,
          mod1 = require("react-native/Libraries/Renderer/shims/ReactNative"),
          _mod_default_createPortal1;
        g.__tamagui_portal_create = (_mod_default_createPortal1 = mod1 == null || (_mod_default1 = mod1.default) === null || _mod_default1 === void 0 ? void 0 : _mod_default1.createPortal) !== null && _mod_default_createPortal1 !== void 0 ? _mod_default_createPortal1 : mod1.createPortal;
      } catch (err) {
        console.info("Note: error importing native portal, native portals disabled", err);
      }
    }
  };
//# sourceMappingURL=native-portal.native.js.map
