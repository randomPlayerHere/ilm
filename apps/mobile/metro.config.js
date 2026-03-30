const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

// Redirect @react-native-google-signin/google-signin to a stub only when running
// in Expo Go (EXPO_GO=true). Production and dev-client builds use the real module.
if (process.env.EXPO_GO === "true") {
  const mockPath = path.resolve(__dirname, "src/mocks/google-signin-mock.ts");
  config.resolver.resolveRequest = (context, moduleName, platform) => {
    if (moduleName === "@react-native-google-signin/google-signin") {
      return { filePath: mockPath, type: "sourceFile" };
    }
    return context.resolveRequest(context, moduleName, platform);
  };
}

module.exports = config;
