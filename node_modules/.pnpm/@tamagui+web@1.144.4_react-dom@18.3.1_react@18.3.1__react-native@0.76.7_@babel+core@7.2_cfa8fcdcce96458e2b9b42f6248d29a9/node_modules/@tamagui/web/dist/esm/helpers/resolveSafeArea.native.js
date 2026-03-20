var safeAreaEdges = {
  $safeAreaTop: "top",
  $safeAreaBottom: "bottom",
  $safeAreaLeft: "left",
  $safeAreaRight: "right"
};
function resolveSafeAreaValue(value) {
  var edge = safeAreaEdges[value];
  if (edge) {
    var g = globalThis,
      state = g.__tamagui_native_safe_area_state__;
    return state?.enabled && state.initialMetrics ? state.initialMetrics.insets[edge] : 0;
  }
}
export { resolveSafeAreaValue };
//# sourceMappingURL=resolveSafeArea.native.js.map
