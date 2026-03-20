function resolveEffectivePseudoTransition(prev, next, pseudoTransitions, baseTransition) {
  if (!pseudoTransitions) return baseTransition;
  const prevState = prev || {
    hover: !1,
    press: !1,
    focus: !1,
    groups: {}
  };
  if (next.press && !prevState.press && pseudoTransitions.pressStyle) return pseudoTransitions.pressStyle;
  if (next.hover && !prevState.hover && pseudoTransitions.hoverStyle) return pseudoTransitions.hoverStyle;
  if (next.focus && !prevState.focus && pseudoTransitions.focusStyle) return pseudoTransitions.focusStyle;
  for (const key in pseudoTransitions) if (key.startsWith("$group-")) {
    const match = key.match(/^\$group-(.+)-(hover|press|focus)$/);
    if (!match) continue;
    const groupName = match[1],
      pseudoType = match[2],
      nextGroupPseudo = next.group?.[groupName]?.pseudo,
      prevGroupPseudo = prevState.groups?.[groupName];
    if (nextGroupPseudo?.[pseudoType] && !prevGroupPseudo?.[pseudoType]) return pseudoTransitions[key];
  }
  return baseTransition;
}
function extractPseudoState(state) {
  const groups = {};
  if (state.group) for (const groupName in state.group) {
    const pseudo = state.group[groupName]?.pseudo;
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
export { extractPseudoState, resolveEffectivePseudoTransition };
//# sourceMappingURL=pseudoTransitions.mjs.map
