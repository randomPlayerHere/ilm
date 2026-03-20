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
var pseudoTransitions_exports = {};
__export(pseudoTransitions_exports, {
  extractPseudoState: () => extractPseudoState,
  resolveEffectivePseudoTransition: () => resolveEffectivePseudoTransition
});
module.exports = __toCommonJS(pseudoTransitions_exports);
function resolveEffectivePseudoTransition(prev, next, pseudoTransitions, baseTransition) {
  if (!pseudoTransitions) return baseTransition;
  var prevState = prev || {
    hover: !1,
    press: !1,
    focus: !1,
    groups: {}
  };
  if (next.press && !prevState.press && pseudoTransitions.pressStyle) return pseudoTransitions.pressStyle;
  if (next.hover && !prevState.hover && pseudoTransitions.hoverStyle) return pseudoTransitions.hoverStyle;
  if (next.focus && !prevState.focus && pseudoTransitions.focusStyle) return pseudoTransitions.focusStyle;
  for (var key in pseudoTransitions) if (key.startsWith("$group-")) {
    var _next_group_groupName,
      _next_group,
      _prevState_groups,
      match = key.match(/^\$group-(.+)-(hover|press|focus)$/);
    if (!match) continue;
    var groupName = match[1],
      pseudoType = match[2],
      nextGroupPseudo = (_next_group = next.group) === null || _next_group === void 0 || (_next_group_groupName = _next_group[groupName]) === null || _next_group_groupName === void 0 ? void 0 : _next_group_groupName.pseudo,
      prevGroupPseudo = (_prevState_groups = prevState.groups) === null || _prevState_groups === void 0 ? void 0 : _prevState_groups[groupName];
    if (nextGroupPseudo?.[pseudoType] && !prevGroupPseudo?.[pseudoType]) return pseudoTransitions[key];
  }
  return baseTransition;
}
function extractPseudoState(state) {
  var groups = {};
  if (state.group) for (var groupName in state.group) {
    var _state_group_groupName,
      pseudo = (_state_group_groupName = state.group[groupName]) === null || _state_group_groupName === void 0 ? void 0 : _state_group_groupName.pseudo;
    pseudo && (groups[groupName] = {
      hover: pseudo.hover,
      press: pseudo.press,
      focus: pseudo.focus
    });
  }
  return {
    hover: state.hover,
    press: state.press,
    focus: state.focus,
    groups
  };
}
//# sourceMappingURL=pseudoTransitions.native.js.map
