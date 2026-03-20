var borderStyles = /* @__PURE__ */new Set(["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset", "none", "hidden"]);
function parseBorderShorthand(value) {
  if (value === "none" || value === "0") return [["borderTopWidth", 0], ["borderRightWidth", 0], ["borderBottomWidth", 0], ["borderLeftWidth", 0], ["borderStyle", "solid"]];
  var parts = value.trim().split(/\s+/),
    borderWidth,
    borderStyle,
    borderColor,
    _iteratorNormalCompletion = !0,
    _didIteratorError = !1,
    _iteratorError = void 0;
  try {
    for (var _iterator = parts[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = !0) {
      var part = _step.value;
      if (borderStyles.has(part)) borderStyle = part;else if (/^[\d.]+(?:px|em|rem|%|pt|vw|vh)?$/.test(part)) {
        var num = parseFloat(part);
        borderWidth = part.endsWith("px") || !part.match(/[a-z%]/i) ? num : part;
      } else borderColor = part;
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
  return borderWidth !== void 0 && (result.push(["borderTopWidth", borderWidth]), result.push(["borderRightWidth", borderWidth]), result.push(["borderBottomWidth", borderWidth]), result.push(["borderLeftWidth", borderWidth])), borderStyle !== void 0 && result.push(["borderStyle", borderStyle]), borderColor !== void 0 && (result.push(["borderTopColor", borderColor]), result.push(["borderRightColor", borderColor]), result.push(["borderBottomColor", borderColor]), result.push(["borderLeftColor", borderColor])), result.length > 0 ? result : void 0;
}
export { parseBorderShorthand };
//# sourceMappingURL=parseBorderShorthand.native.js.map
