"use strict";

var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf,
  __hasOwnProp = Object.prototype.hasOwnProperty;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", {
    value: mod,
    enumerable: !0
  }) : target, mod)),
  __toCommonJS = mod => __copyProps(__defProp({}, "__esModule", {
    value: !0
  }), mod);
var useSwitchNative_native_exports = {};
__export(useSwitchNative_native_exports, {
  useSwitchNative: () => useSwitchNative
});
module.exports = __toCommonJS(useSwitchNative_native_exports);
var import_jsx_runtime = require("react/jsx-runtime"),
  import_core = require("@tamagui/core"),
  import_focusable = require("@tamagui/focusable"),
  React = __toESM(require("react"), 1),
  import_react_native = require("react-native");
function useSwitchNative(props) {
  var {
    id,
    disabled,
    native,
    nativeProps,
    checked,
    setChecked
  } = props;
  React.useEffect(function () {
    if (id && !disabled) return (0, import_focusable.registerFocusable)(id, {
      focusAndSelect: function () {
        setChecked(function (value) {
          return !value;
        });
      },
      focus: function () {}
    });
  }, [id, disabled, setChecked]);
  var renderNative = (0, import_core.shouldRenderNativePlatform)(native);
  return renderNative === "android" || renderNative === "ios" ? /* @__PURE__ */(0, import_jsx_runtime.jsx)(import_react_native.Switch, {
    value: checked,
    onValueChange: setChecked,
    ...nativeProps
  }) : null;
}
//# sourceMappingURL=useSwitchNative.native.js.map
