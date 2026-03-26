import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { GradingCard } from "../GradingCard";
import type { GradingJobWithResultResponse } from "@ilm/contracts";

// Suppress Animated warning about useNativeDriver in test env
jest.mock("react-native/Libraries/Animated/NativeAnimatedHelper", () => ({}), { virtual: true });

const COMPLETED_RESULT: GradingJobWithResultResponse = {
  job_id: "job_1",
  artifact_id: "art_1",
  assignment_id: "asgn_1",
  status: "completed",
  attempt_count: 1,
  submitted_at: "2026-03-26T00:00:00Z",
  completed_at: "2026-03-26T00:00:01Z",
  result: {
    proposed_score: "85/100",
    rubric_mapping: { Clarity: "Excellent", Logic: "Good" },
    draft_feedback: "Great effort shown throughout.",
    generated_at: "2026-03-26T00:00:01Z",
    confidence_level: "high",
    confidence_score: 0.95,
    confidence_reason: null,
    practice_recommendations: [],
  },
  is_approved: false,
};

describe("GradingCard", () => {
  describe("skeleton state (uploading/processing)", () => {
    it("renders without score text when status is uploading", () => {
      render(
        <GradingCard status="uploading" result={null} photoUri={null} error={null} />,
      );
      expect(screen.queryByText("85/100")).toBeNull();
    });

    it("renders without score text when status is processing", () => {
      render(
        <GradingCard status="processing" result={null} photoUri={null} error={null} />,
      );
      expect(screen.queryByText("85/100")).toBeNull();
    });
  });

  describe("completed state", () => {
    it("shows the score when completed", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri="file://test.jpg" error={null} />,
      );
      expect(screen.getByText("85/100")).toBeTruthy();
    });

    it("shows confidence badge 'High' for high confidence", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri="file://test.jpg" error={null} />,
      );
      expect(screen.getByText("High")).toBeTruthy();
    });

    it("shows 'Medium' badge for medium confidence", () => {
      const medResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: { ...COMPLETED_RESULT.result!, confidence_level: "medium", confidence_score: 0.6 },
      };
      render(
        <GradingCard status="completed" result={medResult} photoUri={null} error={null} />,
      );
      expect(screen.getByText("Medium")).toBeTruthy();
    });

    it("shows 'Low' badge for low confidence", () => {
      const lowResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: { ...COMPLETED_RESULT.result!, confidence_level: "low", confidence_score: 0.2 },
      };
      render(
        <GradingCard status="completed" result={lowResult} photoUri={null} error={null} />,
      );
      expect(screen.getByText("Low")).toBeTruthy();
    });

    it("shows AI feedback text", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri="file://test.jpg" error={null} />,
      );
      expect(screen.getByText("Great effort shown throughout.")).toBeTruthy();
    });

    it("rubric criteria are hidden by default", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri={null} error={null} />,
      );
      expect(screen.queryByText("Clarity")).toBeNull();
      expect(screen.queryByText("Logic")).toBeNull();
      expect(screen.getByText(/Rubric breakdown/)).toBeTruthy();
    });

    it("rubric criteria appear after pressing the toggle", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri={null} error={null} />,
      );
      fireEvent.press(screen.getByText(/Rubric breakdown/));
      expect(screen.getByText("Clarity")).toBeTruthy();
      expect(screen.getByText("Logic")).toBeTruthy();
    });

    it("shows fallback message when completed but result.result is null", () => {
      const nullResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: null,
      };
      render(
        <GradingCard status="completed" result={nullResult} photoUri={null} error={null} />,
      );
      expect(screen.getByText("No grading result available")).toBeTruthy();
    });
  });

  describe("failed state", () => {
    it("shows error message when status is failed", () => {
      render(
        <GradingCard status="failed" result={null} photoUri={null} error="AI grading failed" />,
      );
      expect(screen.getByText("Couldn't analyze this one")).toBeTruthy();
      expect(screen.getByText("AI grading failed")).toBeTruthy();
    });
  });
});
