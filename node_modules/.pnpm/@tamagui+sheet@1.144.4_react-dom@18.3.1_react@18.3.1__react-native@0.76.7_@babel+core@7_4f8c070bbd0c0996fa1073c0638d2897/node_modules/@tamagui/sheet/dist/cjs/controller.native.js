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
var controller_exports = {};
__export(controller_exports, {
  SheetController: () => import_SheetController.SheetController,
  SheetControllerContext: () => import_useSheetController.SheetControllerContext,
  useSheetController: () => import_useSheetController.useSheetController
});
module.exports = __toCommonJS(controller_exports);
var import_SheetController = require("./SheetController.native.js"),
  import_useSheetController = require("./useSheetController.native.js");
//# sourceMappingURL=controller.native.js.map
