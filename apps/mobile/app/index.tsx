import { Redirect } from "expo-router";

/**
 * Root route — redirects to auth screen.
 * After auth, user is redirected to their role-scoped group.
 */
export default function Index() {
  return <Redirect href="/auth" />;
}
