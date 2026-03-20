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
var GestureSheetContext_exports = {};
__export(GestureSheetContext_exports, {
  GestureSheetProvider: () => GestureSheetProvider,
  useGestureSheetContext: () => useGestureSheetContext
});
module.exports = __toCommonJS(GestureSheetContext_exports);
var import_react = require("react"),
  import_jsx_runtime = require("react/jsx-runtime");
const GestureSheetContext = (0, import_react.createContext)(null);
function useGestureSheetContext() {
  return (0, import_react.useContext)(GestureSheetContext);
}
function GestureSheetProvider({
  children,
  isDragging,
  blockPan,
  setBlockPan,
  panGesture,
  panGestureRef
}) {
  const value = {
    panGesture,
    panGestureRef,
    isDragging,
    blockPan,
    setBlockPan
  };
  return /* @__PURE__ */(0, import_jsx_runtime.jsx)(GestureSheetContext.Provider, {
    value,
    children
  });
}