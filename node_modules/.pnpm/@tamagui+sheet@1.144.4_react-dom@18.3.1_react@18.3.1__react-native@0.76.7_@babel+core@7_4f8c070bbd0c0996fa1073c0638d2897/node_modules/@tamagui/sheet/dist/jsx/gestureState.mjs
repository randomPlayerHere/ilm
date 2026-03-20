import { getGestureHandler } from "@tamagui/native";
function isGestureHandlerEnabled() {
  return getGestureHandler().isEnabled;
}
function getGestureHandlerState() {
  return getGestureHandler().state;
}
function setGestureHandlerState(updates) {
  getGestureHandler().set(updates);
}
const setGestureState = setGestureHandlerState;
export { getGestureHandlerState, isGestureHandlerEnabled, setGestureHandlerState, setGestureState };
//# sourceMappingURL=gestureState.mjs.map
