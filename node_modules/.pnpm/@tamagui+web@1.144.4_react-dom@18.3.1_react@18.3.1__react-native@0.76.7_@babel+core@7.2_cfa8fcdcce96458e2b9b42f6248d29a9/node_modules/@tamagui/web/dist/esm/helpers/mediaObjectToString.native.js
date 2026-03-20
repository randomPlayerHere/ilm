function camelToHyphen(str) {
  return str.replace(/[A-Z]/g, function (m) {
    return `-${m.toLowerCase()}`;
  }).toLowerCase();
}
var cache = /* @__PURE__ */new WeakMap();
function mediaObjectToString(query) {
  if (typeof query == "string") return query;
  if (cache.has(query)) return cache.get(query);
  var res = Object.entries(query).map(function (param) {
    var [feature, value] = param;
    return feature = camelToHyphen(feature), typeof value == "string" ? `(${feature}: ${value})` : (typeof value == "number" && /[height|width]$/.test(feature) && (value = `${value}px`), `(${feature}: ${value})`);
  }).join(" and ");
  return cache.set(query, res), res;
}
export { mediaObjectToString };
//# sourceMappingURL=mediaObjectToString.native.js.map
