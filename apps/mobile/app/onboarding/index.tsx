import { useState, useCallback } from "react";
import { Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Haptics from "expo-haptics";
import { YStack, XStack, Text, Button, Input, Spinner } from "tamagui";
import { SkeletonLoader } from "@ilm/ui";
import { colors, spacing, fontSizes, fontWeights } from "@ilm/design-tokens";
import { useAuth } from "../../src/contexts/AuthContext";
import { markOnboardingComplete, setNotifPref } from "../../src/services/onboarding-wizard-state";
import {
  createClass,
  listClasses,
  addStudent,
  getLinkedChildren,
} from "../../src/services/onboarding-service";
import type { ClassResponse, LinkedChildResponse } from "@ilm/contracts";

// ─── Progress indicator ───────────────────────────────────────────────────────

function StepIndicator({ step, total }: { step: number; total: number }) {
  return (
    <Text fontSize={fontSizes.sm} color={colors.textTertiary} textAlign="center">
      Step {step + 1} of {total}
    </Text>
  );
}

// ─── Teacher wizard ───────────────────────────────────────────────────────────

function TeacherWizard({
  step,
  setStep,
  token,
  onComplete,
}: {
  step: number;
  setStep: (s: number) => void;
  token: string;
  onComplete: () => Promise<void>;
}) {
  const TOTAL = 3;

  // Step 1 state
  const [classes, setClasses] = useState<ClassResponse[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(false);
  const [selectedClass, setSelectedClass] = useState<ClassResponse | null>(null);
  const [creatingClass, setCreatingClass] = useState(false);
  const [newClassName, setNewClassName] = useState("");
  const [newClassSubject, setNewClassSubject] = useState("");
  const [classError, setClassError] = useState<string | null>(null);
  const [classLoaded, setClassLoaded] = useState(false);

  // Step 2 state
  const [studentName, setStudentName] = useState("");
  const [studentGrade, setStudentGrade] = useState("");
  const [addingStudent, setAddingStudent] = useState(false);
  const [studentCount, setStudentCount] = useState(0);
  const [studentError, setStudentError] = useState<string | null>(null);

  const loadClasses = useCallback(async () => {
    if (classLoaded) return;
    setLoadingClasses(true);
    try {
      const result = await listClasses(token);
      setClasses(result.classes);
      if (result.classes.length > 0) {
        setSelectedClass(result.classes[0]);
      }
    } catch {
      setClassError("Could not load classes.");
    } finally {
      setLoadingClasses(false);
      setClassLoaded(true);
    }
  }, [token, classLoaded]);

  // Load classes when step 0 is reached
  if (step === 0 && !classLoaded && !loadingClasses) {
    void loadClasses();
  }

  const handleCreateClass = async () => {
    if (!newClassName.trim() || !newClassSubject.trim()) return;
    setCreatingClass(true);
    setClassError(null);
    try {
      const created = await createClass(token, {
        name: newClassName.trim(),
        subject: newClassSubject.trim(),
      });
      setClasses((prev) => [created, ...prev]);
      setSelectedClass(created);
      setNewClassName("");
      setNewClassSubject("");
    } catch {
      setClassError("Failed to create class. Please try again.");
    } finally {
      setCreatingClass(false);
    }
  };

  const handleAddStudent = async (skip: boolean) => {
    if (!skip && (!studentName.trim() || !studentGrade.trim() || !selectedClass)) return;
    if (!skip && selectedClass) {
      setAddingStudent(true);
      setStudentError(null);
      try {
        await addStudent(token, selectedClass.class_id, {
          name: studentName.trim(),
          grade_level: studentGrade.trim(),
        });
        setStudentCount((c) => c + 1);
        setStudentName("");
        setStudentGrade("");
      } catch {
        setStudentError("Failed to add student. Please try again.");
        setAddingStudent(false);
        return;
      }
      setAddingStudent(false);
    }
    setStep(2);
  };

  if (step === 0) {
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={0} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Set Up Your Class
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          Create a new class or continue with an existing one.
        </Text>

        {loadingClasses ? (
          <Spinner color={colors.primary} />
        ) : classes.length > 0 ? (
          <YStack gap={spacing.sm}>
            {classes.map((cls) => (
              <XStack
                key={cls.class_id}
                padding={spacing.md}
                borderRadius={8}
                borderWidth={2}
                borderColor={selectedClass?.class_id === cls.class_id ? colors.primary : colors.border}
                backgroundColor={colors.surface}
                pressStyle={{ opacity: 0.8 }}
                onPress={() => setSelectedClass(cls)}
              >
                <YStack flex={1}>
                  <Text fontSize={fontSizes.md} fontWeight={fontWeights.bold} color={colors.textPrimary}>
                    {cls.name}
                  </Text>
                  <Text fontSize={fontSizes.sm} color={colors.textTertiary}>{cls.subject}</Text>
                </YStack>
              </XStack>
            ))}
          </YStack>
        ) : null}

        <YStack gap={spacing.sm} marginTop={spacing.sm}>
          <Text fontSize={fontSizes.sm} fontWeight={fontWeights.bold} color={colors.textSecondary}>
            Create a new class
          </Text>
          <Input
            placeholder="Class name (e.g. Math Period 3)"
            value={newClassName}
            onChangeText={setNewClassName}
            borderColor={colors.border}
            backgroundColor={colors.surface}
          />
          <Input
            placeholder="Subject (e.g. Mathematics)"
            value={newClassSubject}
            onChangeText={setNewClassSubject}
            borderColor={colors.border}
            backgroundColor={colors.surface}
          />
          {classError && (
            <Text fontSize={fontSizes.sm} color={colors.error ?? colors.textTertiary}>{classError}</Text>
          )}
          <Button
            backgroundColor={colors.primary}
            color="#fff"
            disabled={creatingClass || !newClassName.trim() || !newClassSubject.trim()}
            onPress={handleCreateClass}
          >
            {creatingClass ? <Spinner color="#fff" /> : "Create Class"}
          </Button>
        </YStack>

        <Button
          marginTop="auto"
          backgroundColor={colors.primary}
          color="#fff"
          disabled={!selectedClass}
          onPress={() => setStep(1)}
        >
          Continue
        </Button>
      </YStack>
    );
  }

  if (step === 1) {
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={1} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Add Your First Students
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          Add students to {selectedClass?.name ?? "your class"}, or skip for now.
        </Text>

        <Input
          placeholder="Student name"
          value={studentName}
          onChangeText={setStudentName}
          borderColor={colors.border}
          backgroundColor={colors.surface}
        />
        <Input
          placeholder="Grade level (e.g. Grade 5)"
          value={studentGrade}
          onChangeText={setStudentGrade}
          borderColor={colors.border}
          backgroundColor={colors.surface}
        />
        {studentError && (
          <Text fontSize={fontSizes.sm} color={colors.error ?? colors.textTertiary}>{studentError}</Text>
        )}
        {studentCount > 0 && (
          <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
            {studentCount} student{studentCount !== 1 ? "s" : ""} added
          </Text>
        )}

        <Button
          backgroundColor={colors.primary}
          color="#fff"
          disabled={addingStudent || !studentName.trim() || !studentGrade.trim()}
          onPress={() => handleAddStudent(false)}
        >
          {addingStudent ? <Spinner color="#fff" /> : "Add Student"}
        </Button>

        <Button
          variant="outlined"
          borderColor={colors.border}
          onPress={() => handleAddStudent(true)}
        >
          Skip for now
        </Button>
      </YStack>
    );
  }

  // Step 2: Confirmation
  return (
    <YStack flex={1} padding={spacing.lg} gap={spacing.md} alignItems="center" justifyContent="center">
      <StepIndicator step={2} total={TOTAL} />
      <Text fontSize={40}>🎉</Text>
      <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary} textAlign="center">
        Your class is ready!
      </Text>
      <Text fontSize={fontSizes.md} color={colors.textSecondary} textAlign="center">
        {selectedClass?.name ?? "Your class"} is set up.{"\n"}
        Join code: <Text fontFamily="$mono" color={colors.primary}>{selectedClass?.join_code}</Text>
        {"\n"}
        {studentCount > 0
          ? `${studentCount} student${studentCount !== 1 ? "s" : ""} enrolled.`
          : "Share the join code with students to enroll them."}
      </Text>
      <Button
        marginTop={spacing.lg}
        backgroundColor={colors.primary}
        color="#fff"
        onPress={onComplete}
      >
        Get Started
      </Button>
    </YStack>
  );
}

// ─── Parent wizard ────────────────────────────────────────────────────────────

function ParentWizard({
  step,
  setStep,
  token,
  userId,
  onComplete,
}: {
  step: number;
  setStep: (s: number) => void;
  token: string;
  userId: string;
  onComplete: () => Promise<void>;
}) {
  const TOTAL = 3;
  const [children, setChildren] = useState<LinkedChildResponse[]>([]);
  const [loadingChildren, setLoadingChildren] = useState(false);
  const [childrenLoaded, setChildrenLoaded] = useState(false);
  const [notifEnabled, setNotifEnabled] = useState(true);
  const [savingPref, setSavingPref] = useState(false);
  const [notifError, setNotifError] = useState<string | null>(null);

  const loadChildren = useCallback(async () => {
    if (childrenLoaded) return;
    setLoadingChildren(true);
    try {
      const result = await getLinkedChildren(token);
      setChildren(result.children);
    } catch {
      // Non-fatal — show empty state
    } finally {
      setLoadingChildren(false);
      setChildrenLoaded(true);
    }
  }, [token, childrenLoaded]);

  if (step === 0 && !childrenLoaded && !loadingChildren) {
    void loadChildren();
  }

  const handleSaveNotifPref = async () => {
    setSavingPref(true);
    setNotifError(null);
    try {
      await setNotifPref(userId, notifEnabled);
      await onComplete();
    } catch {
      setNotifError("Couldn't save your preference. Please try again.");
    } finally {
      setSavingPref(false);
    }
  };

  if (step === 0) {
    const child = children[0];
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={0} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Your Linked Child
        </Text>

        {loadingChildren ? (
          <Spinner color={colors.primary} />
        ) : child ? (
          <YStack
            padding={spacing.md}
            borderRadius={12}
            borderWidth={1}
            borderColor={colors.border}
            backgroundColor={colors.surface}
            gap={spacing.sm}
          >
            <Text fontSize={fontSizes.lg} fontWeight={fontWeights.bold} color={colors.textPrimary}>
              {child.student_name}
            </Text>
            {child.class_name && (
              <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
                Class: {child.class_name} · {child.subject}
              </Text>
            )}
          </YStack>
        ) : (
          <YStack
            padding={spacing.md}
            borderRadius={12}
            borderWidth={1}
            borderColor={colors.border}
            backgroundColor={colors.surface}
          >
            <Text fontSize={fontSizes.md} color={colors.textSecondary} textAlign="center">
              No child linked yet.{"\n"}Ask your teacher for an invite link.
            </Text>
          </YStack>
        )}

        <Button
          marginTop="auto"
          backgroundColor={colors.primary}
          color="#fff"
          onPress={() => setStep(1)}
        >
          Continue
        </Button>
      </YStack>
    );
  }

  if (step === 1) {
    const child = children[0];
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={1} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Dashboard Preview
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          {child
            ? `${child.student_name}'s progress will appear here as their teacher grades work.`
            : "Your child's progress will appear here once they're linked."}
        </Text>
        <SkeletonLoader variant="card" />
        <SkeletonLoader variant="card" />
        <SkeletonLoader variant="line" />
        <Button
          marginTop="auto"
          backgroundColor={colors.primary}
          color="#fff"
          onPress={() => setStep(2)}
        >
          Continue
        </Button>
      </YStack>
    );
  }

  // Step 2: Notification preference
  return (
    <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
      <StepIndicator step={2} total={TOTAL} />
      <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
        Stay in the Loop
      </Text>
      <Text fontSize={fontSizes.md} color={colors.textSecondary}>
        Get notified when new grades and progress updates are available.
      </Text>

      <XStack
        padding={spacing.md}
        borderRadius={12}
        borderWidth={1}
        borderColor={notifEnabled ? colors.primary : colors.border}
        backgroundColor={colors.surface}
        alignItems="center"
        justifyContent="space-between"
        pressStyle={{ opacity: 0.8 }}
        onPress={() => setNotifEnabled((v) => !v)}
      >
        <Text fontSize={fontSizes.md} color={colors.textPrimary}>
          Progress notifications
        </Text>
        <Text fontSize={fontSizes.md} color={notifEnabled ? colors.primary : colors.textTertiary}>
          {notifEnabled ? "On" : "Off"}
        </Text>
      </XStack>

      <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
        You can change this in settings at any time.
      </Text>
      {notifError && (
        <Text fontSize={fontSizes.sm} color={colors.error ?? colors.textTertiary}>
          {notifError}
        </Text>
      )}

      <Button
        marginTop="auto"
        backgroundColor={colors.primary}
        color="#fff"
        disabled={savingPref}
        onPress={handleSaveNotifPref}
      >
        {savingPref ? <Spinner color="#fff" /> : "Done"}
      </Button>
    </YStack>
  );
}

// ─── Student wizard ───────────────────────────────────────────────────────────

function StudentWizard({
  step,
  setStep,
  onComplete,
}: {
  step: number;
  setStep: (s: number) => void;
  token: string;
  onComplete: () => Promise<void>;
}) {
  const TOTAL = 2;
  const router = useRouter();

  if (step === 0) {
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={0} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Join Your Class
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          Every great learning journey starts with connecting to your class. Ask your teacher for a join code to get started.
        </Text>

        <Button
          backgroundColor={colors.primary}
          color="#fff"
          onPress={() => {
            router.push({ pathname: "/(student)/join", params: { onboardingReturn: "1" } });
          }}
        >
          Enter Join Code
        </Button>

        <Button
          variant="outlined"
          borderColor={colors.border}
          onPress={() => setStep(1)}
        >
          Skip for now
        </Button>
      </YStack>
    );
  }

  // Step 1: Growth view preview
  return (
    <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
      <StepIndicator step={1} total={TOTAL} />
      <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
        Your Learning Journey Starts Here
      </Text>
      <Text fontSize={fontSizes.md} color={colors.textSecondary}>
        As you complete assignments, your growth and progress will light up right here. You've got this!
      </Text>
      <SkeletonLoader variant="card" />
      <SkeletonLoader variant="card" />
      <SkeletonLoader variant="line" />

      <Button
        marginTop="auto"
        backgroundColor={colors.primary}
        color="#fff"
        onPress={onComplete}
      >
        Let's Go!
      </Button>
    </YStack>
  );
}

// ─── Admin wizard ─────────────────────────────────────────────────────────────

function AdminWizard({
  step,
  setStep,
  orgId,
  onComplete,
}: {
  step: number;
  setStep: (s: number) => void;
  orgId: string;
  onComplete: () => Promise<void>;
}) {
  const TOTAL = 3;

  if (step === 0) {
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={0} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Welcome, Administrator
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          Your organization is ready to set up. Let's get your school connected.
        </Text>
        <YStack
          padding={spacing.md}
          borderRadius={12}
          borderWidth={1}
          borderColor={colors.border}
          backgroundColor={colors.surface}
        >
          <Text fontSize={fontSizes.sm} color={colors.textTertiary}>Organization ID</Text>
          <Text fontSize={fontSizes.md} fontFamily="$mono" color={colors.textPrimary}>{orgId}</Text>
        </YStack>
        <Button
          marginTop="auto"
          backgroundColor={colors.primary}
          color="#fff"
          onPress={() => setStep(1)}
        >
          Continue
        </Button>
      </YStack>
    );
  }

  if (step === 1) {
    return (
      <YStack flex={1} padding={spacing.lg} gap={spacing.md}>
        <StepIndicator step={1} total={TOTAL} />
        <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary}>
          Invite Your First Teacher
        </Text>
        <Text fontSize={fontSizes.md} color={colors.textSecondary}>
          To add teachers to your school:
        </Text>
        <YStack
          padding={spacing.md}
          borderRadius={12}
          borderWidth={1}
          borderColor={colors.border}
          backgroundColor={colors.surface}
          gap={spacing.sm}
        >
          <Text fontSize={fontSizes.md} color={colors.textPrimary}>
            1. Go to the Admin Portal (web)
          </Text>
          <Text fontSize={fontSizes.md} color={colors.textPrimary}>
            2. Navigate to User Management
          </Text>
          <Text fontSize={fontSizes.md} color={colors.textPrimary}>
            3. Send an invitation to their school email
          </Text>
        </YStack>
        <Text fontSize={fontSizes.sm} color={colors.textTertiary}>
          Teacher invitations are sent via the Admin Web Portal. Email sending will be available soon.
        </Text>
        <Button
          marginTop="auto"
          backgroundColor={colors.primary}
          color="#fff"
          onPress={() => setStep(2)}
        >
          Continue
        </Button>
      </YStack>
    );
  }

  // Step 2: Confirmation
  return (
    <YStack flex={1} padding={spacing.lg} gap={spacing.md} alignItems="center" justifyContent="center">
      <StepIndicator step={2} total={TOTAL} />
      <Text fontSize={40}>✅</Text>
      <Text fontSize={fontSizes.xl} fontWeight={fontWeights.bold} color={colors.textPrimary} textAlign="center">
        Your school is set up and ready
      </Text>
      <Text fontSize={fontSizes.md} color={colors.textSecondary} textAlign="center">
        You can now manage users, configure settings, and monitor your school's progress from the admin portal.
      </Text>
      <Button
        marginTop={spacing.lg}
        backgroundColor={colors.primary}
        color="#fff"
        onPress={onComplete}
      >
        Go to Dashboard
      </Button>
    </YStack>
  );
}

// ─── Root onboarding screen ───────────────────────────────────────────────────

export default function OnboardingScreen() {
  const { role, token, userId, orgId, homePath } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams<{ step?: string }>();
  const parsedStep = Number(params.step);
  const initialStep = Number.isInteger(parsedStep) && parsedStep >= 0 ? parsedStep : 0;
  const [step, setStep] = useState(initialStep);

  const handleComplete = async () => {
    if (userId) await markOnboardingComplete(userId);
    if (Platform.OS !== "web") await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    router.replace(homePath as Parameters<typeof router.replace>[0]);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }} edges={["top"]}>
      {role === "teacher" && (
        <TeacherWizard
          step={step}
          setStep={setStep}
          token={token!}
          onComplete={handleComplete}
        />
      )}
      {role === "parent" && (
        <ParentWizard
          step={step}
          setStep={setStep}
          token={token!}
          userId={userId!}
          onComplete={handleComplete}
        />
      )}
      {role === "student" && (
        <StudentWizard
          step={step}
          setStep={setStep}
          token={token!}
          onComplete={handleComplete}
        />
      )}
      {role === "admin" && (
        <AdminWizard
          step={step}
          setStep={setStep}
          orgId={orgId ?? ""}
          onComplete={handleComplete}
        />
      )}
      {!role && null}
    </SafeAreaView>
  );
}
