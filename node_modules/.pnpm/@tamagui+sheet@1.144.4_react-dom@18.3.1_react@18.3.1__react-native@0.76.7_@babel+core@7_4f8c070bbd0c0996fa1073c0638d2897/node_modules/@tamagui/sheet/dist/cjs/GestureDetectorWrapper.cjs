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
var GestureDetectorWrapper_exports = {};
__export(GestureDetectorWrapper_exports, {
  GestureDetectorWrapper: () => GestureDetectorWrapper
});
module.exports = __toCommonJS(GestureDetectorWrapper_exports);
var import_react_native = require("react-native-web"),
  import_gestureState = require("./gestureState.cjs"),
  import_jsx_runtime = require("react/jsx-runtime");
function GestureDetectorWrapper({
  gesture,
  children,
  style
}) {
  const {
    GestureDetector
  } = (0, import_gestureState.getGestureHandlerState)();
  return (0, import_gestureState.isGestureHandlerEnabled)() && GestureDetector && gesture ? /* @__PURE__ */(0, import_jsx_runtime.jsx)(GestureDetector, {
    gesture,
    children: /* @__PURE__ */(0, import_jsx_runtime.jsx)(import_react_native.View, {
      style,
      collapsable: !1,
      children
    })
  }) : /* @__PURE__ */(0, import_jsx_runtime.jsx)(import_react_native.View, {
    style,
    children
  });
}