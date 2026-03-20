export * from "./v5-themes.mjs";
import { subtleChildrenThemes } from "./subtleChildrenThemes.mjs";
import { createV5Theme } from "./v5-themes.mjs";
const themes = createV5Theme({
  childrenThemes: subtleChildrenThemes
});
themes.dark.background0075;
themes.dark_yellow.background0075;
themes.dark.background;
themes.dark.accent1;
themes.dark.nonValid;
export { themes };
//# sourceMappingURL=v5-themes-subtle.mjs.map
