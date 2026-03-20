function resolveRem(value) {
  return value;
}
function isRemValue(value) {
  return typeof value == "string" && value.includes("rem");
}
export { isRemValue, resolveRem };
//# sourceMappingURL=resolveRem.mjs.map
