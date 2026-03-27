import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { GradingCard } from "../GradingCard";
import type { GradingJobWithResultResponse } from "@ilm/contracts";
import type { GradingReviewControls } from "../../hooks/useGradingReview";
import type { GradeApprovalControls } from "../../hooks/useGradeApproval";

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

function makeApprovalControls(overrides?: Partial<GradeApprovalControls>): GradeApprovalControls {
  return {
    approve: jest.fn(),
    isApproving: false,
    isApproved: false,
    approvalError: null,
    ...overrides,
  };
}

function makeReviewControls(overrides?: Partial<GradingReviewControls>): GradingReviewControls {
  return {
    scoreValue: 85,
    scoreInputText: "85",
    displayScore: "85/100",
    feedbackValue: "Great effort shown throughout.",
    increment: jest.fn(),
    decrement: jest.fn(),
    setScore: jest.fn(),
    setFeedback: jest.fn(),
    undoFeedback: jest.fn(),
    ...overrides,
  };
}

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

  describe("completed state — read-only (no reviewControls)", () => {
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

    it("does not show confidence note for high confidence", () => {
      render(
        <GradingCard status="completed" result={COMPLETED_RESULT} photoUri={null} error={null} />,
      );
      expect(screen.queryByText(/please review carefully/)).toBeNull();
    });

    it("shows confidence note for medium confidence", () => {
      const medResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: { ...COMPLETED_RESULT.result!, confidence_level: "medium", confidence_score: 0.6 },
      };
      render(
        <GradingCard status="completed" result={medResult} photoUri={null} error={null} />,
      );
      expect(screen.getByText(/please review carefully/)).toBeTruthy();
    });

    it("shows confidence note for low confidence", () => {
      const lowResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: { ...COMPLETED_RESULT.result!, confidence_level: "low", confidence_score: 0.2 },
      };
      render(
        <GradingCard status="completed" result={lowResult} photoUri={null} error={null} />,
      );
      expect(screen.getByText(/please review carefully/)).toBeTruthy();
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

  describe("completed state — edit mode (with reviewControls)", () => {
    it("renders score input with scoreInputText value", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.getByDisplayValue("85")).toBeTruthy();
    });

    it("renders /100 label next to score input", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.getByText("/100")).toBeTruthy();
    });

    it("calls increment when + button is pressed", () => {
      const controls = makeReviewControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={controls}
        />,
      );
      fireEvent.press(screen.getByRole("button", { name: "Increase score" }));
      expect(controls.increment).toHaveBeenCalledTimes(1);
    });

    it("calls decrement when − button is pressed", () => {
      const controls = makeReviewControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={controls}
        />,
      );
      fireEvent.press(screen.getByRole("button", { name: "Decrease score" }));
      expect(controls.decrement).toHaveBeenCalledTimes(1);
    });

    it("calls setScore when score input changes", () => {
      const controls = makeReviewControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={controls}
        />,
      );
      fireEvent.changeText(screen.getByDisplayValue("85"), "90");
      expect(controls.setScore).toHaveBeenCalledWith("90");
    });

    it("renders feedback TextInput with feedbackValue", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls({ feedbackValue: "Edited feedback." })}
        />,
      );
      expect(screen.getByDisplayValue("Edited feedback.")).toBeTruthy();
    });

    it("calls setFeedback when feedback input changes", () => {
      const controls = makeReviewControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={controls}
        />,
      );
      fireEvent.changeText(
        screen.getByDisplayValue("Great effort shown throughout."),
        "New feedback.",
      );
      expect(controls.setFeedback).toHaveBeenCalledWith("New feedback.");
    });

    it("renders undo button", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.getByRole("button", { name: "Undo feedback to AI original" })).toBeTruthy();
    });

    it("calls undoFeedback when undo button is pressed", () => {
      const controls = makeReviewControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={controls}
        />,
      );
      fireEvent.press(screen.getByRole("button", { name: "Undo feedback to AI original" }));
      expect(controls.undoFeedback).toHaveBeenCalledTimes(1);
    });

    it("shows confidence note for medium confidence in edit mode", () => {
      const medResult: GradingJobWithResultResponse = {
        ...COMPLETED_RESULT,
        result: { ...COMPLETED_RESULT.result!, confidence_level: "medium", confidence_score: 0.6 },
      };
      render(
        <GradingCard
          status="completed"
          result={medResult}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.getByText(/please review carefully/)).toBeTruthy();
    });

    it("does not show confidence note for high confidence in edit mode", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.queryByText(/please review carefully/)).toBeNull();
    });

    it("rubric toggle still works in edit mode", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
        />,
      );
      expect(screen.queryByText("Clarity")).toBeNull();
      fireEvent.press(screen.getByText(/Rubric breakdown/));
      expect(screen.getByText("Clarity")).toBeTruthy();
    });
  });

  describe("approval controls", () => {
    it("renders Approve button when reviewControls and approvalControls present and !isApproved", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={makeApprovalControls({ isApproved: false })}
        />,
      );
      expect(screen.getByRole("button", { name: "Approve grade" })).toBeTruthy();
    });

    it("does not render Approve button when approvalControls is null", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={null}
        />,
      );
      expect(screen.queryByRole("button", { name: "Approve grade" })).toBeNull();
    });

    it("Approve button is disabled and shows 'Approving...' when isApproving=true", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={makeApprovalControls({ isApproving: true })}
        />,
      );
      expect(screen.getByText("Approving...")).toBeTruthy();
      expect(screen.getByRole("button", { name: "Approve grade" })).toBeDisabled();
    });

    it("shows 'Approved ✓' text when isApproved=true and no Approve button", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={makeApprovalControls({ isApproved: true })}
        />,
      );
      expect(screen.getByText("Approved ✓")).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Approve grade" })).toBeNull();
    });

    it("renders approvalError text when set", () => {
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={makeApprovalControls({ approvalError: "Approval failed" })}
        />,
      );
      expect(screen.getByText("Approval failed")).toBeTruthy();
    });

    it("tapping Approve calls approvalControls.approve", () => {
      const controls = makeApprovalControls();
      render(
        <GradingCard
          status="completed"
          result={COMPLETED_RESULT}
          photoUri={null}
          error={null}
          reviewControls={makeReviewControls()}
          approvalControls={controls}
        />,
      );
      fireEvent.press(screen.getByRole("button", { name: "Approve grade" }));
      expect(controls.approve).toHaveBeenCalledTimes(1);
    });
  });
});
