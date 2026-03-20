import { PixelRatio } from "react-native";
import { getConfig } from "../config.native.js";
var remRegex = /(-?[\d.]+)rem/g;
function resolveRem(value) {
  var _config_settings,
    config = getConfig(),
    _config_settings_remBaseFontSize,
    baseFontSize = (_config_settings_remBaseFontSize = config == null || (_config_settings = config.settings) === null || _config_settings === void 0 ? void 0 : _config_settings.remBaseFontSize) !== null && _config_settings_remBaseFontSize !== void 0 ? _config_settings_remBaseFontSize : 16;
  if (value.endsWith("rem") && !value.includes(" ")) {
    var numericValue = Number.parseFloat(value);
    if (!Number.isNaN(numericValue)) return PixelRatio.getFontScale() * baseFontSize * numericValue;
  }
  for (var result = 0, match; (match = remRegex.exec(value)) !== null;) {
    var numericValue1 = Number.parseFloat(match[1]);
    Number.isNaN(numericValue1) || (result += PixelRatio.getFontScale() * baseFontSize * numericValue1);
  }
  return remRegex.lastIndex = 0, result;
}
function isRemValue(value) {
  return typeof value == "string" && value.includes("rem");
}
export { isRemValue, resolveRem };
//# sourceMappingURL=resolveRem.native.js.map
