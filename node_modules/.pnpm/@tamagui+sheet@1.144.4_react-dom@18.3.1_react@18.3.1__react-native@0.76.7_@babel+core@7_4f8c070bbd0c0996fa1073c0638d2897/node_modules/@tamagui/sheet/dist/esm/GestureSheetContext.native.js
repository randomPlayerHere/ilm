import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext } from "react";
var GestureSheetContext = /* @__PURE__ */createContext(null);
function useGestureSheetContext() {
  return useContext(GestureSheetContext);
}
function GestureSheetProvider(param) {
  var {
      children,
      isDragging,
      blockPan,
      setBlockPan,
      panGesture,
      panGestureRef
    } = param,
    value = {
      panGesture,
      panGestureRef,
      isDragging,
      blockPan,
      setBlockPan
    };
  return /* @__PURE__ */_jsx(GestureSheetContext.Provider, {
    value,
    children
  });
}
export { GestureSheetProvider, useGestureSheetContext };
//# sourceMappingURL=GestureSheetContext.native.js.map
