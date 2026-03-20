var outlineStyles = /* @__PURE__ */new Set(["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset", "none", "hidden"]);
function parseOutlineShorthand(value) {
  if (value === "none" || value === "0") return [["outlineWidth", 0], ["outlineStyle", "none"]];
  var parts = value.trim().split(/\s+/),
    outlineWidth,
    outlineStyle,
    outlineColor,
    _iteratorNormalCompletion = !0,
    _didIteratorError = !1,
    _iteratorError = void 0;
  try {
    for (var _iterator = parts[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = !0) {
      var part = _step.value;
      if (outlineStyles.has(part)) outlineStyle = part;else if (/^[\d.]+(?:px|em|rem|%|pt|vw|vh)?$/.test(part)) {
        var num = parseFloat(part);
        outlineWidth = part.endsWith("px") || !part.match(/[a-z%]/i) ? num : part;
      } else outlineColor = part;
    }
  } catch (err) {
    _didIteratorError = !0, _iteratorError = err;
  } finally {
    try {
      !_iteratorNormalCompletion && _iterator.return != null && _iterator.return();
    } finally {
      if (_didIteratorError) throw _iteratorError;
    }
  }
  var result = [];
  return outlineWidth !== void 0 && result.push(["outlineWidth", outlineWidth]), outlineStyle !== void 0 && result.push(["outlineStyle", outlineStyle]), outlineColor !== void 0 && result.push(["outlineColor", outlineColor]), result.length > 0 ? result : void 0;
}
export { parseOutlineShorthand };
//# sourceMappingURL=parseOutlineShorthand.native.js.map
