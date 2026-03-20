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
const IS_FABRIC = typeof global < "u" && !!(global._IS_FABRIC ?? global.nativeFabricUIManager),
  setupNativePortal = () => {
    const g = globalThis;
    if (!g.__tamagui_portal_create) {
      if (IS_FABRIC) {
        try {
          const mod = require("react-native/Libraries/Renderer/shims/ReactFabric");
          g.__tamagui_portal_create = mod?.default?.createPortal ?? mod.createPortal;
        } catch (err) {
          console.info("Note: error importing fabric portal, native portals disabled", err);
        }
        return;
      }
      try {
        const mod = require("react-native/Libraries/Renderer/shims/ReactNative");
        g.__tamagui_portal_create = mod?.default?.createPortal ?? mod.createPortal;
      } catch (err) {
        console.info("Note: error importing native portal, native portals disabled", err);
      }
    }
  };