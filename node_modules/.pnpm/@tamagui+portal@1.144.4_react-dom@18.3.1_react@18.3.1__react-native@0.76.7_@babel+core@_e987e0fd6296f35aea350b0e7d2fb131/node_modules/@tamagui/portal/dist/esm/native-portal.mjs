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
export { setupNativePortal };
//# sourceMappingURL=native-portal.mjs.map
