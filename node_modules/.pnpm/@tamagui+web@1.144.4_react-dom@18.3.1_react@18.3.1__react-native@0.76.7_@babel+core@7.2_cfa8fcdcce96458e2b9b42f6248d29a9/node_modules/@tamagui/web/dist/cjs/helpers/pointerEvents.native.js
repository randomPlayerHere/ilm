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
var pointerEvents_native_exports = {};
__export(pointerEvents_native_exports, {
  usePointerEvents: () => usePointerEvents
});
module.exports = __toCommonJS(pointerEvents_native_exports);
var import_react = require("react"),
  import_helpers = require("@tamagui/helpers");
function usePointerEvents(props, viewProps) {
  var {
      onPointerDown,
      onPointerUp,
      onPointerMove,
      onPointerCancel,
      onPointerEnter,
      onPointerLeave
    } = props,
    hasPointerEvents = onPointerDown || onPointerUp || onPointerMove || onPointerCancel || onPointerEnter || onPointerLeave,
    isInsideRef = (0, import_react.useRef)(!1),
    layoutRef = (0, import_react.useRef)({
      width: 0,
      height: 0
    }),
    isCapturedRef = (0, import_react.useRef)(!1);
  if (hasPointerEvents) {
    var createNormalizedEvent = function (e) {
      var touch = e.nativeEvent,
        _touch_identifier,
        normalized = {
          ...e,
          clientX: touch.pageX,
          clientY: touch.pageY,
          pageX: touch.pageX,
          pageY: touch.pageY,
          offsetX: touch.locationX,
          offsetY: touch.locationY,
          pointerType: "touch",
          pointerId: (_touch_identifier = touch.identifier) !== null && _touch_identifier !== void 0 ? _touch_identifier : 0,
          nativeEvent: touch,
          target: {
            setPointerCapture: function (_pointerId) {
              isCapturedRef.current = !0;
            },
            releasePointerCapture: function (_pointerId) {
              isCapturedRef.current = !1;
            }
          }
        };
      return normalized;
    };
    onPointerDown && (viewProps.onTouchStart = (0, import_helpers.composeEventHandlers)(viewProps.onTouchStart, function (e) {
      onPointerDown(createNormalizedEvent(e));
    })), onPointerUp && (viewProps.onTouchEnd = (0, import_helpers.composeEventHandlers)(viewProps.onTouchEnd, function (e) {
      isCapturedRef.current = !1, onPointerUp(createNormalizedEvent(e));
    })), onPointerMove && (viewProps.onTouchMove = (0, import_helpers.composeEventHandlers)(viewProps.onTouchMove, function (e) {
      var {
          locationX,
          locationY
        } = e.nativeEvent,
        {
          width,
          height
        } = layoutRef.current,
        isInBounds = locationX >= 0 && locationX <= width && locationY >= 0 && locationY <= height;
      (isCapturedRef.current || isInBounds) && onPointerMove(createNormalizedEvent(e));
    })), onPointerCancel && (viewProps.onTouchCancel = (0, import_helpers.composeEventHandlers)(viewProps.onTouchCancel, function (e) {
      isCapturedRef.current = !1, onPointerCancel(createNormalizedEvent(e));
    })), (onPointerEnter || onPointerLeave || onPointerMove) && (viewProps.onLayout = (0, import_helpers.composeEventHandlers)(viewProps.onLayout, function (e) {
      layoutRef.current = {
        width: e.nativeEvent.layout.width,
        height: e.nativeEvent.layout.height
      };
    })), onPointerEnter && (viewProps.onTouchStart = (0, import_helpers.composeEventHandlers)(viewProps.onTouchStart, function (e) {
      var {
          locationX,
          locationY
        } = e.nativeEvent,
        {
          width,
          height
        } = layoutRef.current;
      locationX >= 0 && locationX <= width && locationY >= 0 && locationY <= height && (isInsideRef.current = !0, onPointerEnter(createNormalizedEvent(e)));
    })), onPointerLeave && (viewProps.onTouchMove = (0, import_helpers.composeEventHandlers)(viewProps.onTouchMove, function (e) {
      var {
          locationX,
          locationY
        } = e.nativeEvent,
        {
          width,
          height
        } = layoutRef.current,
        isInside = locationX >= 0 && locationX <= width && locationY >= 0 && locationY <= height;
      isInsideRef.current && !isInside && (isInsideRef.current = !1, onPointerLeave(createNormalizedEvent(e)));
    }), viewProps.onTouchEnd = (0, import_helpers.composeEventHandlers)(viewProps.onTouchEnd, function (e) {
      isInsideRef.current && (isInsideRef.current = !1, onPointerLeave(createNormalizedEvent(e)));
    }));
  }
}
//# sourceMappingURL=pointerEvents.native.js.map
