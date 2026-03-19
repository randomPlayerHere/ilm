import { BrowserRouter, Routes, Route, NavLink, Outlet } from "react-router-dom";
import { colors, spacing, fontSizes, fontWeights, radii } from "@ilm/design-tokens";

function Sidebar() {
  const linkStyle = { display: "block" as const, padding: `${spacing.md}px ${spacing.lg}px`, color: colors.textPrimary, textDecoration: "none" as const };
  const activeStyle = { ...linkStyle, backgroundColor: colors.primary, color: colors.textInverse, borderRadius: radii.md };

  return (
    <nav style={{
      width: 240,
      minHeight: "100vh",
      backgroundColor: colors.surface,
      borderRight: `1px solid ${colors.border}`,
      padding: spacing.lg,
    }}>
      <div style={{ fontSize: fontSizes.xl, fontWeight: fontWeights.semibold, color: colors.primary, marginBottom: spacing["2xl"], padding: `${spacing.sm}px ${spacing.lg}px` }}>
        Teacher OS
      </div>
      <NavLink to="/organizations" style={({ isActive }) => isActive ? activeStyle : linkStyle}>Organizations</NavLink>
      <NavLink to="/users" style={({ isActive }) => isActive ? activeStyle : linkStyle}>Users</NavLink>
      <NavLink to="/roles" style={({ isActive }) => isActive ? activeStyle : linkStyle}>Roles</NavLink>
      <NavLink to="/settings" style={({ isActive }) => isActive ? activeStyle : linkStyle}>Settings</NavLink>
      <NavLink to="/standards" style={({ isActive }) => isActive ? activeStyle : linkStyle}>Standards</NavLink>
    </nav>
  );
}

function AdminLayout() {
  return (
    <div style={{ display: "flex", backgroundColor: colors.background, minHeight: "100vh" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: spacing["2xl"] }}>
        <Outlet />
      </main>
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 style={{ fontSize: fontSizes["2xl"], fontWeight: fontWeights.semibold, color: colors.textPrimary }}>{title}</h1>
      <p style={{ color: colors.textSecondary, marginTop: spacing.sm }}>Coming soon</p>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<Placeholder title="Dashboard" />} />
          <Route path="organizations" element={<Placeholder title="Organizations" />} />
          <Route path="users" element={<Placeholder title="Users" />} />
          <Route path="roles" element={<Placeholder title="Roles" />} />
          <Route path="settings" element={<Placeholder title="Settings" />} />
          <Route path="standards" element={<Placeholder title="Standards" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
