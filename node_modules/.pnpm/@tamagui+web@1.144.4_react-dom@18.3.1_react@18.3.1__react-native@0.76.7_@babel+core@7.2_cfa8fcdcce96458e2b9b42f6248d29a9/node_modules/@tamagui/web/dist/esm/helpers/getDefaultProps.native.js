import { getConfig } from "../config.native.js";
var getDefaultProps = function (staticConfig, propsComponentName) {
  var _conf_defaultProps,
    defaultProps = staticConfig?.defaultProps,
    conf = getConfig(),
    name = propsComponentName || staticConfig?.componentName || (
    // important: this is how we end up getting the defaultProps we set in createTamagui
    staticConfig.isText ? "Text" : "View"),
    userDefaultProps = conf == null || (_conf_defaultProps = conf.defaultProps) === null || _conf_defaultProps === void 0 ? void 0 : _conf_defaultProps[name];
  return userDefaultProps && (defaultProps = defaultProps ? {
    ...userDefaultProps,
    ...defaultProps
  } : userDefaultProps), defaultProps;
};
export { getDefaultProps };
//# sourceMappingURL=getDefaultProps.native.js.map
