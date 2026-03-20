import { useRef } from "react";
import { composeEventHandlers } from "@tamagui/helpers";
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
    isInsideRef = useRef(!1),
    layoutRef = useRef({
      width: 0,
      height: 0
    }),
    isCapturedRef = useRef(!1);
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
    onPointerDown && (viewProps.onTouchStart = composeEventHandlers(viewProps.onTouchStart, function (e) {
      onPointerDown(createNormalizedEvent(e));
    })), onPointerUp && (viewProps.onTouchEnd = composeEventHandlers(viewProps.onTouchEnd, function (e) {
      isCapturedRef.current = !1, onPointerUp(createNormalizedEvent(e));
    })), onPointerMove && (viewProps.onTouchMove = composeEventHandlers(viewProps.onTouchMove, function (e) {
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
    })), onPointerCancel && (viewProps.onTouchCancel = composeEventHandlers(viewProps.onTouchCancel, function (e) {
      isCapturedRef.current = !1, onPointerCancel(createNormalizedEvent(e));
    })), (onPointerEnter || onPointerLeave || onPointerMove) && (viewProps.onLayout = composeEventHandlers(viewProps.onLayout, function (e) {
      layoutRef.current = {
        width: e.nativeEvent.layout.width,
        height: e.nativeEvent.layout.height
      };
    })), onPointerEnter && (viewProps.onTouchStart = composeEventHandlers(viewProps.onTouchStart, function (e) {
      var {
          locationX,
          locationY
        } = e.nativeEvent,
        {
          width,
          height
        } = layoutRef.current;
      locationX >= 0 && locationX <= width && locationY >= 0 && locationY <= height && (isInsideRef.current = !0, onPointerEnter(createNormalizedEvent(e)));
    })), onPointerLeave && (viewProps.onTouchMove = composeEventHandlers(viewProps.onTouchMove, function (e) {
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
    }), viewProps.onTouchEnd = composeEventHandlers(viewProps.onTouchEnd, function (e) {
      isInsideRef.current && (isInsideRef.current = !1, onPointerLeave(createNormalizedEvent(e)));
    }));
  }
}
export { usePointerEvents };
//# sourceMappingURL=pointerEvents.native.js.map
