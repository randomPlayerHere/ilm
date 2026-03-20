import { useRef } from "react";
function useSheetScrollViewGestures(param) {
  var {
      scrollBridge,
      hasScrollableContent,
      scrollEnabled,
      setScrollEnabled
    } = param,
    state = useRef({
      lastPageY: 0,
      dragAt: 0,
      dys: [],
      isScrolling: !1,
      isDraggingScrollArea: !1,
      scrollEngaged: !1,
      prevScrollY: 0,
      handoffOccurred: !1,
      handoffDragOffset: 0
    }),
    release = function () {
      var s = state.current;
      if (s.isDraggingScrollArea) {
        s.isDraggingScrollArea = !1, scrollBridge.scrollStartY = -1, scrollBridge.scrollLock = !1, s.isScrolling = !1, s.scrollEngaged = !1, s.prevScrollY = 0, s.handoffOccurred = !1, s.handoffDragOffset = 0, setScrollEnabled(!0);
        var vy = 0;
        if (s.dys.length) {
          var recentDys = s.dys.slice(-10),
            dist = recentDys.reduce(function (a, b) {
              return a + b;
            }, 0);
          vy = dist / recentDys.length * 0.04;
        }
        s.dys = [], scrollBridge.release({
          dragAt: s.dragAt,
          vy
        });
      }
    },
    onStartShouldSetResponder = function () {
      var s = state.current;
      return scrollBridge.scrollStartY = -1, s.isDraggingScrollArea = !0, s.scrollEngaged = scrollBridge.y > 0, s.prevScrollY = scrollBridge.y, s.handoffOccurred = !1, s.handoffDragOffset = 0, !1;
    },
    onMoveShouldSetResponder = function (e) {
      if (!scrollEnabled) return !1;
      var s = state.current,
        {
          pageY
        } = e.nativeEvent;
      return s.lastPageY === 0 ? (s.lastPageY = pageY, !1) : Math.abs(pageY - s.lastPageY) > 10;
    },
    onResponderMove = function (e) {
      var s = state.current,
        {
          pageY
        } = e.nativeEvent;
      !s.isScrolling && scrollBridge.scrollStartY === -1 && (scrollBridge.scrollStartY = pageY, s.lastPageY = pageY);
      var dragAt = pageY - scrollBridge.scrollStartY,
        dy = pageY - s.lastPageY;
      s.lastPageY = pageY;
      var isDraggingDown = dy > 0,
        isPaneAtTop = scrollBridge.paneY <= scrollBridge.paneMinY + 5,
        currentScrollY = scrollBridge.y;
      currentScrollY > 0 && (s.scrollEngaged = !0);
      var wasScrolledNowAtZero = s.scrollEngaged && s.prevScrollY > 0 && currentScrollY <= 0;
      wasScrolledNowAtZero && !s.handoffOccurred && (s.handoffOccurred = !0, s.handoffDragOffset = 0), s.prevScrollY = currentScrollY;
      var panHandles = !1;
      if (!isPaneAtTop) panHandles = isDraggingDown ? currentScrollY <= 0 || !hasScrollableContent : !0;else if (isDraggingDown) currentScrollY > 0 && hasScrollableContent && !s.handoffOccurred ? panHandles = !1 : panHandles = s.handoffOccurred || wasScrolledNowAtZero || currentScrollY <= 0;else if (panHandles = !hasScrollableContent, !panHandles) {
        s.isScrolling = !0, scrollBridge.scrollLock = !0, setScrollEnabled(!0);
        return;
      }
      if (panHandles) {
        setScrollEnabled(!1);
        var effectiveDragAt = dragAt;
        s.handoffOccurred && (s.handoffDragOffset += dy, effectiveDragAt = s.handoffDragOffset), scrollBridge.drag(effectiveDragAt), s.dragAt = effectiveDragAt, s.dys.push(dy), s.dys.length > 100 && (s.dys = s.dys.slice(-10));
      } else setScrollEnabled(!0);
    };
  return {
    onResponderRelease: release,
    onStartShouldSetResponder,
    onMoveShouldSetResponder,
    onResponderMove
  };
}
export { useSheetScrollViewGestures };
//# sourceMappingURL=useSheetScrollViewGestures.native.js.map
