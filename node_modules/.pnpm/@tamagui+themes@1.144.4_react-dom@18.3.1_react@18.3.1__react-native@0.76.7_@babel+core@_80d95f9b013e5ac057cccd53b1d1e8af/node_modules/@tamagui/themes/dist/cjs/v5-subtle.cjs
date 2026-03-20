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
  },
  __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));
var __toCommonJS = mod => __copyProps(__defProp({}, "__esModule", {
  value: !0
}), mod);
var v5_subtle_exports = {};
__export(v5_subtle_exports, {
  createThemes: () => import_theme_builder.createThemes,
  themes: () => import_generated_v5_subtle.themes,
  tokens: () => import_v5_tokens.tokens,
  v5Templates: () => import_v5_templates.v5Templates
});
module.exports = __toCommonJS(v5_subtle_exports);
var import_theme_builder = require("@tamagui/theme-builder"),
  import_generated_v5_subtle = require("./generated-v5-subtle.cjs"),
  import_v5_templates = require("./v5-templates.cjs");
__reExport(v5_subtle_exports, require("./v5-themes-subtle.cjs"), module.exports);
var import_v5_tokens = require("./v5-tokens.cjs");