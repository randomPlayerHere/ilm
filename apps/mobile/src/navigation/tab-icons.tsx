import { MaterialCommunityIcons } from "@expo/vector-icons";

type IconName = React.ComponentProps<typeof MaterialCommunityIcons>["name"];

interface TabIconEntry {
  active: IconName;
  inactive: IconName;
}

const teacherIcons: Record<string, TabIconEntry> = {
  index: { active: "home", inactive: "home-outline" },
  grade: { active: "clipboard-check", inactive: "clipboard-check-outline" },
  plan: {
    active: "book-open-page-variant",
    inactive: "book-open-page-variant-outline",
  },
  messages: { active: "message", inactive: "message-outline" },
  settings: { active: "dots-horizontal", inactive: "menu" },
};

const parentIcons: Record<string, TabIconEntry> = {
  index: { active: "view-dashboard", inactive: "view-dashboard-outline" },
  progress: { active: "chart-line", inactive: "chart-line-variant" },
  messages: { active: "message", inactive: "message-outline" },
  settings: { active: "cog", inactive: "cog-outline" },
};

const studentIcons: Record<string, TabIconEntry> = {
  index: { active: "trending-up", inactive: "chart-timeline-variant" },
  progress: { active: "chart-line", inactive: "chart-line-variant" },
  tips: { active: "lightbulb", inactive: "lightbulb-outline" },
  settings: { active: "cog", inactive: "cog-outline" },
};

export const roleIcons = {
  teacher: teacherIcons,
  parent: parentIcons,
  student: studentIcons,
} as const;

export function getTabBarIcon(
  role: keyof typeof roleIcons,
  screenName: string,
) {
  const icons = roleIcons[role][screenName];
  if (!icons) return undefined;

  return ({ focused, color, size }: { focused: boolean; color: string; size: number }) => (
    <MaterialCommunityIcons
      name={focused ? icons.active : icons.inactive}
      size={size}
      color={color}
    />
  );
}
