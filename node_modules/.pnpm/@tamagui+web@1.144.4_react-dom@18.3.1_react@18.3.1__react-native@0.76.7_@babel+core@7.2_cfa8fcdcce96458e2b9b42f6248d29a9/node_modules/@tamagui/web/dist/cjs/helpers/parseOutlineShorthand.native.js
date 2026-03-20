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
var parseOutlineShorthand_native_exports = {};
__export(parseOutlineShorthand_native_exports, {
  parseOutlineShorthand: () => parseOutlineShorthand
});
module.exports = __toCommonJS(parseOutlineShorthand_native_exports);
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
//# sourceMappingURL=parseOutlineShorthand.native.js.map
