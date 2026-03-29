import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";

// Mock expo-router
const mockRouterPush = jest.fn();
const mockRouterBack = jest.fn();
jest.mock("expo-router", () => ({
  router: { push: mockRouterPush, back: mockRouterBack },
  useFocusEffect: (cb: () => void) => { cb(); },
  useLocalSearchParams: () => ({ classId: "cls_demo_math_1" }),
}));

// Mock AuthContext
jest.mock("../../src/contexts/AuthContext", () => ({
  useAuth: () => ({ token: "fake-token" }),
}));

// Mock grading-service
jest.mock("../../src/services/grading-service", () => ({
  listAssignments: jest.fn(),
}));

// Mock tamagui Text with plain RN Text
jest.mock("tamagui", () => ({
  Text: ({ children, ...props }: React.PropsWithChildren<object>) => {
    const { Text } = require("react-native");
    return <Text {...props}>{children}</Text>;
  },
}));

// Mock design tokens
jest.mock("@ilm/design-tokens", () => ({
  colors: { background: "#fff", surface: "#f5f5f5", textPrimary: "#000", textSecondary: "#666", primary: "#007aff", border: "#e0e0e0", error: "#ff3b30" },
  fonts: { body: "System", heading: "System" },
  fontWeights: { medium: "500", semibold: "600", bold: "700" },
  spacing: { xs: 4, sm: 8, md: 16, lg: 20, xl: 32 },
}));

// Mock react-native-safe-area-context
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: ({ children }: React.PropsWithChildren<object>) => {
    const { View } = require("react-native");
    return <View>{children}</View>;
  },
}));

import { listAssignments } from "../../src/services/grading-service";
import AssignmentHistoryScreen from "../assignment-history";

const mockListAssignments = listAssignments as jest.MockedFunction<typeof listAssignments>;

beforeEach(() => {
  jest.clearAllMocks();
});

describe("AssignmentHistoryScreen", () => {
  it("renders assignment list after fetch", async () => {
    mockListAssignments.mockResolvedValueOnce({
      assignments: [
        { assignment_id: "asgn_1", class_id: "cls_demo_math_1", title: "Quiz 1", created_at: "2026-03-01T10:00:00Z", artifact_count: 2 },
        { assignment_id: "asgn_2", class_id: "cls_demo_math_1", title: "Quiz 2", created_at: "2026-03-05T10:00:00Z", artifact_count: 1 },
      ],
    });

    const { getByText } = render(<AssignmentHistoryScreen />);

    await waitFor(() => {
      expect(getByText("Quiz 1")).toBeTruthy();
      expect(getByText("Quiz 2")).toBeTruthy();
    });
  });

  it("shows empty state when no assignments", async () => {
    mockListAssignments.mockResolvedValueOnce({ assignments: [] });

    const { getByText } = render(<AssignmentHistoryScreen />);

    await waitFor(() => {
      expect(getByText("No assignments yet.")).toBeTruthy();
    });
  });

  it("shows error state and retry button on fetch failure", async () => {
    mockListAssignments.mockRejectedValueOnce(new Error("Network error"));

    const { getByText } = render(<AssignmentHistoryScreen />);

    await waitFor(() => {
      expect(getByText("Retry")).toBeTruthy();
    });
  });

  it("navigates to assignment-detail when an assignment is tapped", async () => {
    mockListAssignments.mockResolvedValueOnce({
      assignments: [
        { assignment_id: "asgn_1", class_id: "cls_demo_math_1", title: "Quiz 1", created_at: "2026-03-01T10:00:00Z", artifact_count: 1 },
      ],
    });

    const { getByText } = render(<AssignmentHistoryScreen />);

    await waitFor(() => {
      expect(getByText("Quiz 1")).toBeTruthy();
    });

    fireEvent.press(getByText("Quiz 1"));

    expect(mockRouterPush).toHaveBeenCalledWith(
      expect.objectContaining({
        pathname: "/(teacher)/assignment-detail",
        params: expect.objectContaining({ assignmentId: "asgn_1", title: "Quiz 1" }),
      }),
    );
  });

  it("shows loading state initially", () => {
    mockListAssignments.mockReturnValueOnce(new Promise(() => {})); // never resolves
    const { getByText } = render(<AssignmentHistoryScreen />);
    expect(getByText("Loading…")).toBeTruthy();
  });
});
