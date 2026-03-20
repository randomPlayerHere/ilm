export * from "./v5-themes.native.js";
import { subtleChildrenThemes } from "./subtleChildrenThemes.native.js";
import { createV5Theme } from "./v5-themes.native.js";
var themes = createV5Theme({
  childrenThemes: subtleChildrenThemes
});
themes.dark.background0075;
themes.dark_yellow.background0075;
themes.dark.background;
themes.dark.accent1;
themes.dark.nonValid;
export { themes };
//# sourceMappingURL=v5-themes-subtle.native.js.map
