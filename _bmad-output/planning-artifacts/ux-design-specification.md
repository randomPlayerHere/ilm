---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
lastStep: 13
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2026-03-03.md
  - _bmad-output/planning-artifacts/product-brief-ilm-2025-03-01.md
  - _bmad-output/implementation-artifacts/architecture.md
  - _bmad-output/brainstorming/brainstorming-session-2025-03-01.md
---

# UX Design Specification - Teacher OS

**Author:** elephant
**Date:** 2026-03-19

---

<!-- UX design content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

### Project Vision

Teacher OS (ilm) is a mobile-centric AI-driven K-12 education platform built around one question: "Is my child improving?" It delivers a React Native mobile app as the primary interface for teachers (grading and planning), parents (transparency and benchmarks), and students (growth and "level up" experience), with a companion web interface for principals/org managers and administrators. The product combines AI-assisted grading from photos, self-serve progress dashboards, contextual messaging, and curriculum planning — shifting parent-teacher communication from reactive to proactive and self-serve.

### Target Users

| Role | Primary Need | Primary Surface | Context |
|------|-------------|----------------|---------|
| **Teacher** | Grade faster, plan smarter, stop being the bottleneck | Mobile app (phone camera) | Overloaded, 28+ students, hours on grading and parent emails |
| **Parent/Guardian** | Answer "Is my child improving?" without contacting teacher | Mobile app | Anxious, wants transparency, varies in tech literacy |
| **Student** | Understand growth and own their learning | Mobile app | Stressed by grades, wants agency not surveillance |
| **Principal/Org Manager** | Cohort-level data for staffing/PD/curriculum decisions | Companion web | Needs evidence-based decision support, privacy-safe aggregates |
| **Global Admin** | Efficient org/user/role management and onboarding | Companion web | Needs fast school onboarding and issue resolution |

### Key Design Challenges

1. **Five roles, one coherent product** — Each role has fundamentally different goals and workflows. The mobile app must feel tailored per role without becoming five separate apps. Role-scoped navigation and contextual UI are critical.
2. **AI trust and control** — Teachers must feel empowered by AI grading suggestions, not threatened. The review/approve flow must feel like a power tool. AI failure fallback (blurry photo, low confidence) must be seamless with no dead ends.
3. **Information density vs. clarity** — Parents range from highly engaged to barely tech-literate. The "Is my child improving?" answer must be instantly graspable while offering depth for those who want it. Students need the same data reframed as motivating, not stressful.
4. **Mobile-first grading workflow** — The core teacher loop (snap → AI suggests → review → approve) must be fast, thumb-friendly, and completable in under 2 minutes in a noisy classroom.
5. **Onboarding cold-start across roles** — Each role arrives with different expectations. The invite-link → sign-in → value moment chain must be frictionless, delivering core value within 2-3 steps.

### Design Opportunities

1. **"Answer before you ask" transparency** — If the parent dashboard genuinely answers "Is my child improving?" with context (not just a number), it eliminates the most common parent-teacher friction. Competitors show grades; Teacher OS shows understanding.
2. **Growth framing for students** — The "level up" metaphor and improvement trail can make progress feel like a game students own rather than a report card adults impose — a rare empowering student-facing education UX.
3. **Contextual messaging as workflow** — Messages linked to specific students, assignments, and scores turn communication into actionable threads rather than inbox noise — a differentiated pattern few EdTech tools execute well.

## Core User Experience

### Defining Experience

The foundational interaction of Teacher OS is the **teacher grading loop**: capture assignment photo → receive AI-suggested score and feedback → review/adjust → approve for publication. Every other experience in the platform depends on this loop producing data — parent dashboards, student growth views, principal cohort insights, and contextual messaging all flow downstream from teacher-approved grades and feedback. If this loop isn't fast, trustworthy, and thumb-friendly, the entire product stalls.

**Per-role core actions:**

| Role | Core Action | Frequency | Success Feels Like |
|------|-----------|-----------|-------------------|
| Teacher | Snap → AI grade → review → approve | Multiple times daily | "Faster than grading by hand, and the feedback is better" |
| Parent | Open dashboard → see improvement trend → drill into details if needed | Daily to weekly | "I know how my child is doing without asking anyone" |
| Student | Check growth view → see strengths and next steps → act on tip | Weekly | "I know what to work on and I can see I'm getting better" |
| Principal | View cohort trends → filter by grade/subject → identify action areas | Weekly to monthly | "I have evidence for my next staffing or curriculum decision" |
| Admin | Create org → invite teachers → resolve access issues | As needed | "School was live in under an hour" |

### Platform Strategy

**Primary surface: React Native mobile app**
- Teachers, parents, and students interact primarily via mobile
- Camera-native grading workflow leverages device hardware
- Push notifications (FCM/APNs) for configurable alerts and digests
- Offline photo queue + cached dashboard views for poor-connectivity resilience
- Client-side image compression (~2MP) before upload

**Secondary surface: Companion web interface**
- Principals/org managers use web for cohort analytics and organizational oversight
- Admins use web for user/role/org management and safety configuration
- Wider screen real estate suits data-dense dashboards and administrative tables

**Platform principles:**
- Mobile is the default design target; web adapts the same data for larger screens
- Touch-first interaction patterns; thumb-zone-aware layout for key actions
- Offline-tolerant: never block the teacher workflow due to connectivity
- Progressive disclosure: simple surface, depth on demand

### Effortless Interactions

**Must feel zero-friction:**
1. **Photo capture → AI grading** — One tap to open camera, snap, and receive AI suggestion. No multi-step upload wizard. Image quality feedback is inline (e.g., "Photo is blurry — retake?") not a separate validation screen.
2. **Parent sign-up via invite link** — Tap invite link → Google sign-in → child already linked → dashboard visible. No manual child-linking, no code entry, no configuration.
3. **Notification preferences** — Set once during onboarding, adjust anytime from a single settings screen. System respects cadence immediately — no "changes take effect tomorrow."
4. **Contextual messaging** — Teacher taps a student's grade → "Message parent about this" → thread auto-linked to student + assignment. No manual context-setting.

**Should happen automatically:**
- AI grading job queued on photo upload (no "submit for grading" button)
- Dashboard data refreshes in background (silent push)
- Offline photos auto-upload when connectivity resumes
- Weekly digest assembled and sent per parent preference without teacher action

### Critical Success Moments

1. **Teacher first grading session** — Teacher snaps a photo, sees AI-suggested score and feedback within seconds, adjusts one thing, approves. Realizes: "This just saved me 5 minutes per assignment." If this moment fails (slow AI, bad suggestion, confusing UI), teacher abandons the product.
2. **Parent first dashboard view** — Parent opens app after invite, immediately sees a clear trend indicator answering "Is my child improving?" with a simple up/down/steady signal plus one-sentence explanation. If this moment fails (confusing charts, no data, generic "welcome" screen), parent never returns.
3. **Student first growth check** — Student opens app and sees their improvement trail with strengths highlighted and one clear next step. Feels ownership, not judgment. If this moment fails (grade-heavy, red/negative framing, feels like a report card), student disengages.
4. **Admin first school onboarding** — Admin creates org, invites teachers via email, teachers land in guided setup. Total time: under 30 minutes to a functioning school. If this moment fails (complex setup, unclear roles, broken invites), school never launches.
5. **AI grading failure recovery** — AI returns low confidence or fails. Teacher sees clear reason ("Handwriting unclear in bottom section"), taps "Grade manually" or "Retake photo" — no lost context, no dead end. If this moment fails (cryptic error, lost work), trust in AI pipeline breaks permanently.

### Experience Principles

1. **Data flows downstream, value flows up** — Every teacher action (grading, planning, messaging) generates data that automatically surfaces as insight for parents, students, and principals. No role should have to re-enter or re-request information that already exists in the system.
2. **Answer first, details on demand** — Lead every screen with the answer to the user's primary question (teacher: "What do I need to grade?", parent: "Is my child improving?", student: "Where am I growing?"). Details, charts, and history are one tap deeper, never blocking the headline.
3. **Trust through transparency and control** — Teachers approve before anything is visible. Parents see explanations, not just numbers. Students see growth framing, not punitive scores. Every role trusts the system because they understand what they're seeing and control what others see.
4. **Mobile-native, not mobile-squeezed** — Design for the phone first. Grading uses the camera. Navigation is thumb-friendly. Key actions are one-tap. The web interface is a complementary surface for data-dense admin/analytics work, not a "full version" that mobile compromises on.
5. **Graceful degradation, never dead ends** — Offline? Photos queue. AI fails? Manual fallback. No data yet? Guided onboarding. Every edge case has a forward path — users are never stuck.

## Desired Emotional Response

### Primary Emotional Goals

| Role | Primary Emotion | Trigger Moment | What They'd Say |
|------|----------------|----------------|-----------------|
| **Teacher** | Empowered efficiency | Completing a grading session in a fraction of the time | "I just did 30 minutes of work in 10. This thing gets me." |
| **Parent** | Informed reassurance | Seeing the improvement trend on first dashboard visit | "I know what's happening. I can actually help my kid." |
| **Student** | Capable ownership | Seeing growth trail with clear next steps | "I'm getting better and I know what to do next." |
| **Principal** | Evidence-backed confidence | Using cohort data to support a staffing or PD decision | "I can defend this decision with real data." |
| **Admin** | Effortless competence | Onboarding a school in under 30 minutes | "That was easy. Nothing broke." |

### Emotional Journey Mapping

**Teacher emotional arc:**
- **Discovery/Onboarding:** Curious but skeptical → "AI grading? Let me see if it actually works"
- **First grading session:** Surprise → "That suggestion was actually good"
- **Ongoing use:** Relief and flow → "Grading isn't the worst part of my day anymore"
- **When AI fails:** Unfazed → "OK, I'll retake or grade this one myself" (not frustrated or stuck)
- **Returning daily:** Anticipation → "Let me knock these out before lunch"

**Parent emotional arc:**
- **Invite link:** Easy welcome → "That was painless, I'm already seeing my kid's data"
- **First dashboard view:** Clarity → "Up arrow. She's improving. OK, good."
- **Drilling into details:** Understanding → "Oh, word problems are the weak spot. That makes sense."
- **Receiving a digest:** Calm awareness → "Good to know, no action needed this week"
- **Messaging teacher:** Partnership → "I have a specific question, not a vague worry"

**Student emotional arc:**
- **First login:** Curiosity → "What is this? It doesn't look like a gradebook."
- **Seeing growth view:** Pride → "I went up in three areas since last month"
- **Reading next steps:** Agency → "OK, I'll try that tip before the quiz"
- **After acting on a tip:** Accomplishment → "It worked. I can see the difference."
- **Returning weekly:** Routine ownership → "Let me check where I'm at"

### Micro-Emotions

**Critical micro-emotions to cultivate:**
- **Confidence over confusion** — Every screen answers one question clearly. Navigation never requires guessing.
- **Trust over skepticism** — AI suggestions show reasoning. Teachers retain final authority. Parents see explanations, not black-box scores.
- **Accomplishment over frustration** — Every workflow has a completable endpoint. No half-finished states, no ambiguous "pending" limbo.
- **Belonging over isolation** — Contextual messaging connects roles around shared student context. Parents feel like partners, not outsiders.

**Micro-emotions to prevent:**
- **Surveillance anxiety (students)** — Growth framing, not deficit framing. "You improved in X" not "You failed at Y."
- **Alert fatigue (parents)** — Configurable cadence. Default to weekly digest, not instant everything.
- **Replacement fear (teachers)** — AI is positioned as "your assistant suggested..." not "the system graded..."
- **Helplessness (any role)** — Every error state has a forward action. Every empty state has guidance.

### Design Implications

| Emotional Goal | UX Design Approach |
|---------------|-------------------|
| Teacher empowerment | AI suggestions presented as editable drafts, not verdicts. "Suggested score: 85" with one-tap adjust. Teacher's name on the final grade, not "AI-graded." |
| Parent reassurance | Hero trend indicator (up/down/steady arrow) at top of dashboard. One-sentence explanation below. Details progressive-disclosed, never forced. |
| Student ownership | Growth language throughout: "You've improved," "Next challenge," "Your streak." No red/fail colors for below-average. Warm palette for growth areas. |
| Principal confidence | Data presented with context: "5th grade math trending down 8% this quarter" not raw charts. Actionable framing, not just visualization. |
| Admin competence | Wizard-style onboarding with clear progress indicators. Confirmation at each step. "School is live" success state with checklist of what's ready. |
| Trust (all roles) | Teacher approval gate clearly visible. "Approved by Ms. Rodriguez" on every published grade. Explanations attached to every score parents and students see. |
| No dead ends (all roles) | Every error shows: what happened, why, and what to do next. Offline states show cached data with "Last updated" timestamp, not blank screens. |

### Emotional Design Principles

1. **Assistant, not authority** — AI is always positioned as helping the human, never deciding for them. Language: "Suggested," "Draft," "Your call." Never: "Determined," "Final," "System score."
2. **Growth over judgment** — Every data visualization frames change as a journey, not a verdict. Upward trends are celebrated. Downward trends are framed as "areas for focus" with actionable next steps, not failure indicators.
3. **Calm over urgent** — Default notification cadence is digest, not instant. Visual design uses calm, warm tones. Alerts are reserved for genuinely time-sensitive events, not engagement hooks.
4. **Partnership over hierarchy** — Parent-teacher messaging feels like collaboration, not reporting. Student views feel like coaching, not monitoring. Principal views feel like insight, not surveillance.
5. **Completion over complexity** — Every workflow has a clear "done" state with confirmation. Progress indicators on multi-step flows. Celebrate small completions (grade approved, school onboarded, first tip acted on).

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**1. Duolingo — Growth framing and return engagement**

| Aspect | What They Do Well | Relevance to Teacher OS |
|--------|------------------|------------------------|
| Progress visualization | XP, streaks, skill trees that show exactly where you are and what's next | Student growth view: show improvement trail and clear next steps |
| Encouraging language | "You're on fire!" "Great streak!" — never punitive, always forward | Student and parent-facing copy: growth language, celebrate upward trends |
| Onboarding | Value in first 60 seconds — pick a language, do a lesson, feel progress | All roles: guided onboarding delivering value within 2-3 steps |
| Return hooks | Streak maintenance, daily reminders calibrated to user preference | Configurable notification cadence — not annoying, but habit-forming |
| Simplicity | One core action per screen; complexity hidden behind simple choices | Mobile-first design: answer first, details on demand |

**2. ClassDojo — Parent-teacher communication baseline**

| Aspect | What They Do Well | Where Teacher OS Improves |
|--------|------------------|--------------------------|
| Parent onboarding | Invite code → sign up → see child immediately | Teacher OS: invite link → Google sign-in → child pre-linked → dashboard (fewer steps) |
| Behavior feedback loop | Teachers tap positive/negative behavior points in real-time | Teacher OS: AI-assisted grading with richer feedback and explanations, not just points |
| Class feed / story | Shared class updates parents can see | Teacher OS: contextual messaging tied to specific students and assignments, not broadcast |
| Simple UI | Very low-friction for non-tech-savvy parents | Teacher OS: same simplicity target, but with deeper longitudinal data underneath |
| **Gap: no "Is my child improving?" answer** | Shows individual behavior points but no trend, no longitudinal view, no "why" | Teacher OS: hero trend indicator + explanation + strengths/weaknesses = the core differentiator |
| **Gap: no AI-assisted workflow** | All grading/feedback is fully manual | Teacher OS: AI grading loop saves teacher time and generates richer data |

**3. Google Lens / Camera Apps — Capture-and-process interaction**

| Aspect | What They Do Well | Relevance to Teacher OS |
|--------|------------------|------------------------|
| One-tap camera launch | Camera opens instantly, no intermediate screens | Teacher grading: one tap to camera from assignment list |
| Inline recognition feedback | Results appear overlaid on camera view or immediately after capture | AI grading: show suggestion immediately after snap, no separate "processing" screen if possible |
| Image quality guidance | Subtle hints when photo is too dark, blurry, or angled | Teacher capture: inline "Photo is blurry — retake?" before submitting to AI |
| Graceful fallback | If recognition fails, offers alternative actions (search, translate, etc.) | AI failure: clear reason + "Retake" or "Grade manually" — no dead ends |
| Speed | Results feel instant even when processing happens in background | Perceived performance: show skeleton/progress immediately, deliver results within seconds |

### Transferable UX Patterns

**Navigation Patterns:**
- **Role-scoped tab bar (Duolingo-style):** Bottom navigation with 4-5 role-specific tabs. Teacher: Home / Grade / Plan / Messages / More. Parent: Dashboard / Progress / Messages / Settings. Student: Growth / Tips / Progress. Simple, thumb-friendly, never more than one tap to core action.
- **Progressive disclosure (Duolingo):** Lead with the headline answer, reveal detail on tap. Parent dashboard: trend arrow first, then scores, then per-subject breakdown, then individual assignments.

**Interaction Patterns:**
- **Snap-and-suggest (Google Lens):** Camera opens full-screen, snap returns to a suggestion card overlaid on the photo. Teacher adjusts score/feedback inline, approves with one tap. No multi-screen wizard.
- **Contextual action sheets (ClassDojo):** Tapping a student or grade surfaces relevant actions (message parent, view history, add note) in a bottom sheet. No navigation to a separate "actions" screen.
- **Inline status transitions:** Grade states (draft → AI suggested → teacher approved → published) shown as a subtle status badge, not a separate workflow view.

**Visual Patterns:**
- **Warm growth palette (Duolingo):** Greens and golds for progress, warm neutrals for baseline, soft amber for "focus areas." No red for below-average — aligns with growth-over-judgment principle.
- **Hero metric card (health/finance apps):** A single large number or indicator at the top of the screen answering the primary question. Parent: trend arrow + one sentence. Teacher: "12 assignments to review." Student: "You improved in 3 areas this month."
- **Skeleton loading (modern mobile apps):** Content-shaped placeholders while data loads. Never a blank screen or a full-screen spinner.

### Anti-Patterns to Avoid

1. **Dashboard overload (many EdTech tools)** — Showing every metric, chart, and number on one screen. Parents don't need 15 charts; they need one trend arrow and the option to explore. Apply "answer first, details on demand" rigorously.
2. **Notification spam (ClassDojo trap)** — Defaulting to instant notifications for everything. Creates alert fatigue and parent resentment. Default to weekly digest; let users opt into higher frequency.
3. **Generic empty states** — "No data yet. Check back later." Every empty state should guide the user toward the action that creates data (teacher: "Snap your first assignment to see AI grading in action"; parent: "Your child's teacher hasn't posted grades yet — you'll see them here").
4. **AI black box** — Showing an AI-generated score without explanation. Teachers won't trust what they can't understand. Always show reasoning alongside suggestion.
5. **Desktop-first, mobile-adapted** — Designing for web and shrinking to mobile. Teacher OS is mobile-first; the web interface is the adaptation, not the other way around.
6. **Surveillance framing for students** — Showing students what adults see about them in the same format adults see it. Student view must be reframed: growth language, coaching tone, ownership — not a surveillance dashboard.

### Design Inspiration Strategy

**Adopt directly:**
- Duolingo's growth/streak visualization language for student views
- Google Lens's one-tap camera → inline result pattern for teacher grading
- Bottom tab navigation with role-scoped tabs (mobile standard)
- Skeleton loading for all data-dependent screens
- Hero metric card pattern for role-specific primary screens

**Adapt for Teacher OS:**
- ClassDojo's parent invite flow → simplify further with pre-linked invite URLs (no code entry)
- Duolingo's gamification → lighter version for MVP (progress bars + encouraging language, no XP/badges/avatar yet)
- Health app longitudinal charts → adapt for academic progress with growth framing (no red/fail coloring)

**Avoid explicitly:**
- ClassDojo's shallow analytics (no longitudinal "improving?" answer)
- EdTech dashboard overload (too many charts, no headline answer)
- Notification-heavy defaults (respect calm-over-urgent principle)
- AI scores without explanation (breaks trust principle)
- Desktop-first responsive design (mobile-native is the requirement)

## Design System Foundation

### Design System Choice

**Tamagui** — A universal design system for React Native and web with optimized, beautiful components, fluid animations, and powerful theming.

### Rationale for Selection

| Factor | Assessment |
|--------|-----------|
| **Visual quality** | Best-in-class among RN cross-platform options. Fluid animations, polished component defaults, modern aesthetic out of the box. |
| **Cross-platform** | Same components compile to optimized native (iOS/Android) and web — true write-once for mobile app and companion web interface. |
| **Theming** | Powerful token-based theming system. Supports the warm growth palette, role-specific color accents, and light/dark modes natively. |
| **Performance** | Compiles styles at build time to optimized platform-specific output — no runtime style overhead on mobile. |
| **Accessibility** | Components built on React Native accessibility primitives. WCAG AA compliance achievable through semantic usage and token-level contrast enforcement. |
| **Team velocity** | Lean team (6-9 contributors) gets polished components fast. Reduces need for a dedicated designer to make things "look right." |
| **Customization** | Fully themeable without fighting the framework. Teacher OS gets its own visual identity, not a Material/Google look. |
| **Community/maturity** | Growing adoption in the RN ecosystem. Smaller community than MUI/Paper, but active development and strong documentation. |

### Implementation Approach

**Monorepo integration:**
- `packages/design-tokens` — Central token definitions (colors, spacing, typography, radii, shadows) consumed by Tamagui theme config
- `packages/ui-mobile` — Shared Tamagui components used across mobile app role surfaces (teacher, parent, student)
- `packages/ui-web` — Web-specific Tamagui component variants for admin and principal companion interface
- Both mobile and web apps import from shared packages, ensuring visual consistency

**Token-driven theming:**
- **Base theme:** Warm, calm palette aligned with emotional design principles (no clinical blues/grays, no harsh reds)
- **Role accents:** Subtle color differentiation per role context (teacher: productive teal, parent: reassuring green, student: energizing gold, admin: neutral slate)
- **Growth palette:** Greens/golds for progress, warm amber for "focus areas," never red for below-average
- **Typography scale:** Clear hierarchy optimized for mobile readability — large hero metrics, comfortable body text, compact but legible data tables
- **Dark mode:** Supported from day one via Tamagui's native theme switching

**Component strategy:**
- Use Tamagui's built-in components for standard UI (buttons, cards, inputs, sheets, tabs, dialogs)
- Build custom composite components for domain-specific patterns:
  - `GradingCard` — photo + AI suggestion + adjust controls + approve action
  - `TrendIndicator` — hero up/down/steady arrow with one-line explanation
  - `GrowthTimeline` — longitudinal progress visualization with growth framing
  - `ContextualMessageComposer` — message input pre-linked to student/assignment context
  - `OnboardingWizard` — role-specific step-through with progress indicator
- Skeleton loading variants for every data-dependent component

**Animation strategy:**
- Tamagui's built-in animation driver for micro-interactions (button press, card transitions, sheet slides)
- Subtle celebration animations for key success moments (grade approved, trend improved, onboarding complete)
- Smooth transitions between screens — no jarring jumps
- Loading → content transitions using skeleton-to-real-data morphing

### Customization Strategy

**Visual identity direction:**
- Modern, warm, and approachable — not clinical or corporate
- Rounded corners (medium radii) for friendly feel
- Generous whitespace for breathing room on mobile
- Card-based layouts for scannable content blocks
- Subtle depth (soft shadows) rather than flat or heavy material elevation
- Photography/illustration style: warm, inclusive, education-focused (for empty states and onboarding)

**Accessibility customizations:**
- All color tokens validated for WCAG 2.1 AA contrast ratios at the token level
- Focus indicators visible and consistent across all interactive elements
- Touch targets minimum 44x44pt on mobile per iOS/Android guidelines
- Screen reader labels on all custom components
- Reduced motion mode respects OS-level accessibility settings

**Platform-specific adaptations:**
- Mobile: bottom sheet modals, swipe gestures where natural, haptic feedback on key actions (grade approved)
- Web: hover states, keyboard navigation, wider layouts for data tables and admin views
- Both: consistent tokens, typography, and component behavior — different layout, same visual language

## Defining Experience

### The One-Liner

**Teacher OS: "Snap a photo of student work and get it graded in seconds."**

This is the interaction teachers demo to colleagues, parents hear about from other parents, and administrators see in the first pitch. Everything else in the product — parent dashboards, student growth views, principal analytics, contextual messaging — flows from this single moment working flawlessly.

**Secondary defining experience (the spreader):** *"Open the app and instantly know if your child is improving."* This is what makes parents tell other parents. The teacher experience generates the data; the parent experience generates the word of mouth.

### User Mental Model

**Teacher mental model — "Grading is my biggest time sink":**
- Current reality: Stack of papers, red pen, manual entry into gradebook, then field parent emails asking "what did my kid get?"
- Mental model they bring: Grading = slow, tedious, solitary. Any tool that touches grading must prove it's faster than the red pen within the first use.
- Expectation: "Show me it works on MY students' handwriting, not a demo." Skepticism is high — AI grading sounds too good to be true.
- Key insight: Teachers don't want AI to replace their judgment. They want AI to do the tedious part (read handwriting, check against rubric, draft feedback) so they can do the expert part (adjust, contextualize, approve).

**Parent mental model — "I shouldn't have to chase information":**
- Current reality: Wait for report cards, email the teacher, get a vague "doing fine" response, worry in between.
- Mental model they bring: School communication = delayed, teacher-gated, opaque. Progress = report card grades.
- Expectation: "Just tell me if my kid is OK." They don't want to learn a dashboard — they want an answer.
- Key insight: Parents will only adopt if the first screen gives them the answer. If they have to navigate, filter, or interpret charts, they'll revert to emailing the teacher.

**Student mental model — "Grades happen TO me":**
- Current reality: Get a paper back with a score. Maybe a comment. No clear connection to what to do next.
- Mental model they bring: Grades = judgment from adults. Feedback = "try harder."
- Expectation: "Is this going to make me feel bad?" Defensive until proven otherwise.
- Key insight: Students engage when the framing shifts from "here's your score" to "here's how you're growing and what to try next." Agency, not surveillance.

### Success Criteria

**Teacher grading loop success:**

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Time from camera tap to approved grade | Under 2 minutes per assignment | In-app timing telemetry |
| AI suggestion accuracy (teacher accepts without major edit) | 70%+ of suggestions accepted with minor or no adjustment | Approval vs. override rate |
| First-session "aha" moment | Teacher approves first AI-graded assignment and says "that was fast" | Onboarding completion + immediate second use |
| Failure recovery | Teacher never loses work when AI fails | Zero data-loss incidents on failure paths |
| Return behavior | Teacher uses grading loop daily within first week | Daily active usage after onboarding |

**Parent dashboard success:**

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Time to answer "Is my child improving?" | Under 5 seconds from app open | Screen load time + eye-tracking/scroll depth |
| First-visit comprehension | Parent understands trend without explanation | Onboarding survey / usability test |
| Self-serve resolution | 80%+ of "how is my kid doing?" questions answered without messaging teacher | Message volume relative to dashboard views |
| Return behavior | Parent checks dashboard at least weekly | Weekly active usage |

**Student growth view success:**

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Emotional response | "This is helping me" not "this is watching me" | Usability test sentiment / survey |
| Actionability | Student can name one thing to work on after viewing | Post-session survey |
| Return behavior | Student checks growth view weekly | Weekly active usage |

### Novel UX Patterns

**Novel — Camera-to-grade pipeline:**
This is the most innovative interaction in the product. No mainstream EdTech tool offers snap → AI grade → teacher approve as a single mobile flow. It combines established patterns (camera capture, card-based results) in a novel way (AI grading with teacher-in-the-loop approval).

- **Teaching the pattern:** No tutorial needed — camera is universally understood. The novelty is what happens AFTER the snap. Show the AI suggestion immediately overlaid on the photo (like Google Lens results), making the connection between "what I photographed" and "what the AI thinks" viscerally clear.
- **Familiar metaphor:** "It's like having a teaching assistant who pre-grades everything and you just check their work."

**Established — Hero metric dashboard:**
The parent "Is my child improving?" screen uses a well-established pattern (hero metric card from health/finance apps) applied to a new domain. No user education needed — big arrow up means good, down means attention needed.

**Established + twist — Contextual messaging:**
Messaging is familiar, but auto-linking to student + assignment context is a twist. The composer pre-fills context so the teacher never starts from scratch. Pattern feels familiar (chat), outcome is differentiated (every message has academic context attached).

### Experience Mechanics

**1. Teacher Grading Loop — Step by Step:**

**Initiation:**
- Teacher opens app → Home screen shows "12 assignments to review" with a prominent "Grade" action button
- OR teacher taps the persistent camera FAB (floating action button) available on all teacher screens
- Camera opens full-screen immediately — no intermediate selection screen

**Interaction:**
- Teacher positions phone over student work → viewfinder shows alignment guides
- Tap shutter → photo captured → brief "Analyzing..." skeleton card appears over the photo
- Within seconds: `GradingCard` slides up showing:
  - Thumbnail of captured photo (tappable to zoom)
  - "Suggested score: 87/100" with one-tap +/- adjustment
  - AI-generated feedback summary (2-3 sentences, editable)
  - Rubric breakdown if rubric was attached to assignment
  - Confidence indicator (high/medium/low — if low, explains why: "Some handwriting unclear in Q3")
- Teacher reviews: adjusts score if needed (inline slider or number input), edits feedback text if needed
- "Approve & Publish" button at bottom — single tap

**Feedback:**
- On approve: subtle success animation (checkmark + brief haptic pulse)
- Card transitions to "Published" state with teacher's name: "Graded by Ms. Rodriguez"
- Next ungraded assignment auto-loads if batch grading — continuous flow, no navigation back
- Progress indicator: "4 of 12 graded" visible at top

**Completion:**
- After last assignment: "All caught up!" celebration screen with summary ("12 assignments graded in 18 minutes")
- Published grades now visible to linked parents and students
- Notification dispatched per parent cadence preferences (instant/digest/off)

**Error/Edge Cases:**
- Blurry photo: inline "Photo may be blurry — Retake?" before AI processing (saves time and API cost)
- AI failure: "Couldn't analyze this one — [reason]" + "Retake Photo" and "Grade Manually" buttons. Manual grading shows same card layout without AI suggestions, preserving workflow context
- AI low confidence: shows suggestion with amber confidence badge + "AI is less certain about this one — please review carefully"
- Offline: photo queued locally with "Will grade when connected" badge. Teacher can continue capturing. Photos auto-submit on reconnect

**2. Parent Dashboard — Step by Step:**

**Initiation:**
- Parent opens app → lands directly on child's dashboard (no navigation required if single child linked)
- If multiple children: child selector at top, last-viewed child pre-selected

**Interaction:**
- Hero section: `TrendIndicator` showing improvement trend (up arrow / down arrow / steady) + one-sentence explanation ("Ava is improving in Math this month, with strong computation skills")
- Below hero: subject cards showing per-subject trend + latest score
- Tap any subject → drill into `GrowthTimeline` showing longitudinal view + strengths/weaknesses
- Tap any assignment → see score + AI-generated explanation + teacher feedback
- "Message Teacher" contextual action available from any assignment detail

**Feedback:**
- Data updates via background refresh (silent push). Pull-to-refresh for manual update
- New grades appear with subtle "New" badge
- Trend indicators animate when data changes (arrow direction transition)

**Completion:**
- No explicit "done" — parent browses as long as they want
- The question "Is my child improving?" is answered before any scrolling
- Digest notification reminds parent to check back per their configured cadence

## Design Directions

### Chosen Direction: "Clear Path" — Confident minimalism with purposeful color

**Philosophy:** Clean, spacious, and modern. The design trusts whitespace and typography hierarchy to do the heavy lifting. Color is used sparingly and intentionally — sage green for actions and trust, gold reserved for celebrations and student growth moments. Every element earns its place on screen. Trust comes from clarity and precision — users feel confident because the interface is confident.

**Visual Characteristics:**

| Element | Specification |
|---------|--------------|
| **Overall feel** | Professional, uncluttered, focused, warm-but-not-soft |
| **Surfaces** | Clean white cards (`#FFFFFF`) on warm off-white background (`#FAFAF5`) — subtle depth without visual noise |
| **Card treatment** | Minimal shadow (`elevation-1`), subtle warm border (`#E8E4DC`), `radius-md` (12px). No gradients. No decorative elements. |
| **Color usage** | Restrained. Sage green (`#2D6A4F`) for primary actions and navigation. Gold (`#DDA15E`) for student growth moments and celebrations only. Most of the interface is neutral — color draws the eye to what matters. |
| **Typography** | Strong hierarchy is the primary design tool. `hero` size for the one number that matters. Clear size/weight steps between levels. Inter throughout. |
| **Icons** | Outlined, medium weight (Lucide icon set). Precise, not playful. Consistent 24px size in navigation, 20px inline. |
| **Empty states** | Simple line illustrations with one accent color. Minimal, purposeful, guiding — not decorative. |
| **Imagery** | Photography/illustrations used only for onboarding and empty states. The product surface is data and typography, not pictures. |
| **Borders & dividers** | Warm neutral (`#E8E4DC`), 1px, used sparingly. Prefer spacing over lines to separate content. |
| **Interactive states** | Subtle background shift on press (not color change). Green fill for primary buttons, outlined for secondary. Disabled states use `text-muted` with reduced opacity. |

**Per-Role Expression:**

The "Clear Path" direction adapts its expression per role while maintaining the same visual system:

| Role | Expression | Why |
|------|-----------|-----|
| **Teacher** | Most utilitarian. Dense information, efficient layouts, minimal decoration. Camera and grading flows are streamlined — no unnecessary steps or visual flourish. | Teachers value speed. The interface should feel like a sharp tool. |
| **Parent** | Slightly warmer. Hero trend indicator is large and prominent. Explanatory text is generous. Cards have a bit more breathing room. | Parents need reassurance. Clarity = trust. |
| **Student** | Warmest variant. Gold accents appear more frequently. Growth language is prominent. Progress visualizations use the most expressive treatment in the system (still clean, but celebratory). | Students need encouragement within the same clean framework. |
| **Principal/Admin** | Most neutral. Slate/gray accents dominate. Data tables and charts are crisp and information-dense. Functional, evidence-based feel. | Decision-makers want data, not decoration. |

**Animation Philosophy:**

| Context | Treatment |
|---------|-----------|
| **Screen transitions** | Clean slide or fade. 200-250ms duration. No bounce, no overshoot. |
| **Data loading** | Skeleton placeholders that match content shape. Subtle shimmer (warm tone, not cool gray). |
| **Success confirmations** | Brief checkmark fade-in + optional haptic. No confetti, no elaborate celebration. |
| **Student growth celebrations** | The one exception to restraint: a slightly more expressive animation when a student levels up or hits a milestone. Still tasteful — a gentle scale-up + gold shimmer, not fireworks. |
| **Trend indicator updates** | Smooth number/arrow transitions when data changes. Feels alive, not static. |
| **Reduced motion** | All animations replaced with instant state changes. No degradation of information. |

**Why "Clear Path" works for Teacher OS:**

1. **Efficiency signals trust** — A clean, uncluttered interface tells teachers "we respect your time." No visual noise competing with the task at hand.
2. **Clarity signals competence** — Parents trust an interface that's easy to read. If the app looks clear and organized, the data feels more reliable.
3. **Restraint allows growth moments to shine** — Because the baseline is calm and minimal, the moments where gold/celebration appears (student growth, milestones) feel genuinely special.
4. **Scales across roles** — The same visual system serves a teacher batch-grading 30 assignments and a parent checking one child's trend. Minimalism accommodates both density and simplicity.
5. **Ages well** — Trendy, expressive design dates quickly. Clean minimalism with warm touches stays fresh. For an EdTech product that schools adopt for years, longevity matters.

## Visual Design Foundation

### Color System

**Design philosophy:** Comforting, trustworthy, warm. The palette should feel like a calm conversation with someone who knows what they're talking about — not a flashy app, not a clinical tool.

**Primary Palette:**

| Token | Hex | Usage | Feel |
|-------|-----|-------|------|
| `primary` | `#2D6A4F` | Primary actions, navigation accents, teacher-facing highlights | Deep sage green — trustworthy, grounded, natural |
| `primary-light` | `#52B788` | Success states, positive trends, growth indicators | Vibrant sage — optimistic without being loud |
| `primary-dark` | `#1B4332` | Headers, emphasis text, active states | Forest — authoritative but warm |

**Secondary Palette:**

| Token | Hex | Usage | Feel |
|-------|-----|-------|------|
| `secondary` | `#DDA15E` | Warm accents, student-facing highlights, celebration moments | Honey gold — encouraging, rewarding |
| `secondary-light` | `#FEFAE0` | Light backgrounds, card surfaces, hover states | Warm cream — soft, inviting |
| `secondary-dark` | `#BC6C25` | Secondary emphasis, badges | Deep amber — grounded warmth |

**Semantic Colors:**

| Token | Hex | Usage | Note |
|-------|-----|-------|------|
| `success` | `#52B788` | Approved grades, positive trends, completed actions | Same as primary-light — growth = success |
| `focus` | `#E9C46A` | Areas needing attention, medium confidence AI | Warm amber — attention without alarm |
| `caution` | `#F4A261` | Low confidence AI, connectivity issues | Soft orange — notice, don't panic |
| `error` | `#E07A5F` | System errors, failed uploads, blocked actions | Terracotta — serious but not harsh (NOT bright red) |
| `info` | `#7FB8B0` | Informational badges, neutral indicators | Soft teal — calm, factual |

**Role Accent Colors:**

| Role | Accent | Hex | Application |
|------|--------|-----|------------|
| Teacher | Productive teal | `#2D6A4F` | Primary green — their actions power the system |
| Parent | Reassuring sage | `#52B788` | Lighter green — everything is visible and OK |
| Student | Energizing gold | `#DDA15E` | Warm gold — growth, achievement, your journey |
| Principal | Grounded slate | `#6C757D` | Neutral — data-focused, not emotional |
| Admin | Cool neutral | `#495057` | Functional — tools, not feelings |

**Surface Colors:**

| Token | Hex (Light) | Hex (Dark) | Usage |
|-------|-------------|------------|-------|
| `background` | `#FAFAF5` | `#1A1A1A` | App background — warm off-white, not clinical white |
| `surface` | `#FFFFFF` | `#252525` | Cards, sheets, elevated content |
| `surface-dim` | `#F0EDE6` | `#1F1F1F` | Subtle section separation, input backgrounds |
| `text-primary` | `#2C2C2C` | `#F0EDE6` | Body text — warm dark, not pure black |
| `text-secondary` | `#6B6B6B` | `#A0A0A0` | Supporting text, labels, timestamps |
| `text-muted` | `#9B9B9B` | `#707070` | Placeholders, disabled states |
| `border` | `#E8E4DC` | `#333333` | Card borders, dividers — warm, subtle |

**Critical color rules:**
- NO bright red for below-average student performance. Use `focus` (warm amber) for "areas to improve"
- NO clinical white (`#FFFFFF`) as app background — use warm off-white (`#FAFAF5`)
- NO pure black (`#000000`) for text — use warm dark (`#2C2C2C`)
- ALL color combinations validated for WCAG 2.1 AA contrast (4.5:1 for body text, 3:1 for large text and UI components)

### Typography System

**Design philosophy:** Readable, friendly, professional. Should feel like a well-designed book — easy on the eyes for extended reading (teacher feedback, parent explanations) but with clear hierarchy for quick scanning (dashboard metrics, grade summaries).

**Font selection:**

| Role | Font | Rationale |
|------|------|-----------|
| **Primary (headings + UI)** | **Inter** | Clean, modern, highly readable at all sizes. Excellent on mobile. Open source. Tamagui-friendly. Conveys trust and competence without being cold. |
| **Secondary (body + long text)** | **Inter** | Single font family for simplicity and performance. Weight and size variations provide all needed hierarchy. |
| **Monospace (data/code)** | **JetBrains Mono** | For score displays, data tables, and any numerical emphasis. Clear digit differentiation. |

**Type Scale (mobile-first):**

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `hero` | 36px | 700 (Bold) | 1.2 | Hero metrics — trend arrows, primary scores |
| `h1` | 28px | 700 (Bold) | 1.25 | Screen titles |
| `h2` | 22px | 600 (Semibold) | 1.3 | Section headers |
| `h3` | 18px | 600 (Semibold) | 1.35 | Card titles, sub-sections |
| `body` | 16px | 400 (Regular) | 1.5 | Primary body text, explanations, feedback |
| `body-small` | 14px | 400 (Regular) | 1.45 | Secondary text, labels, metadata |
| `caption` | 12px | 500 (Medium) | 1.4 | Timestamps, badges, status indicators |
| `score` | 32px (mono) | 700 (Bold) | 1.1 | Numerical scores, percentages |

**Web scale adjustment:** Companion web interface uses same tokens with +2px on `h1` and `h2` for larger screen readability.

**Typography rules:**
- Minimum touch-target text: 14px (no text below 12px anywhere)
- Maximum line width: 65 characters for body text (readability)
- AI-generated feedback text always in `body` size — never smaller, always readable
- Score numbers use monospace font for clear digit alignment in tables and cards

### Spacing & Layout Foundation

**Base unit:** 4px grid. All spacing values are multiples of 4px.

**Spacing scale:**

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight internal padding (badge padding, icon gaps) |
| `sm` | 8px | Compact spacing (between related items in a list) |
| `md` | 16px | Standard spacing (card internal padding, form field gaps) |
| `lg` | 24px | Section spacing (between cards, between sections) |
| `xl` | 32px | Major section separation |
| `2xl` | 48px | Screen-level vertical breathing room |

**Layout principles:**

| Principle | Implementation |
|-----------|---------------|
| **Generous breathing room** | Cards use `md` (16px) internal padding minimum. Never cramped. |
| **Card-based architecture** | All content lives in rounded cards (`border-radius: 12px`) on the `surface-dim` background. Scannable, tappable, distinct. |
| **Thumb-zone awareness** | Primary actions (Approve, Camera FAB, Send Message) positioned in bottom third of screen. Navigation tabs at bottom. |
| **Single-column mobile** | No side-by-side layouts on mobile except for small metric pairs. Vertical scroll is the primary navigation pattern. |
| **Responsive web grid** | Companion web uses 12-column grid. Dashboard cards arrange in 2-3 column layouts. Admin tables use full width. |

**Component spacing patterns:**

| Pattern | Spec |
|---------|------|
| Card stack (e.g., assignment list) | `lg` (24px) gap between cards |
| Card internal sections | `md` (16px) between sections within a card |
| Form fields | `md` (16px) between fields |
| Hero metric to supporting content | `lg` (24px) |
| Bottom tab bar height | 56px + safe area inset |
| Camera FAB size | 56px diameter, `lg` (24px) from bottom-right edge |
| Touch targets | Minimum 44x44px hit area on all interactive elements |

**Corner radii:**

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 8px | Buttons, input fields, badges |
| `radius-md` | 12px | Cards, sheets, dialogs |
| `radius-lg` | 16px | Modal sheets, image containers |
| `radius-full` | 9999px | Avatars, circular icons, FAB |

**Elevation/depth:**

| Token | Shadow | Usage |
|-------|--------|-------|
| `elevation-1` | `0 1px 3px rgba(0,0,0,0.08)` | Cards resting on background |
| `elevation-2` | `0 4px 12px rgba(0,0,0,0.10)` | Floating action button, bottom sheets |
| `elevation-3` | `0 8px 24px rgba(0,0,0,0.12)` | Modal dialogs, overlays |

Shadows use warm tones (not cool gray) to maintain the comforting feel.

### Accessibility Considerations

**Color accessibility:**
- All text/background combinations meet WCAG 2.1 AA (4.5:1 for body, 3:1 for large text)
- Never rely on color alone to convey meaning — always pair with icons, labels, or patterns (e.g., trend arrow + color + text)
- Growth palette avoids red/green pairing that fails for color-blind users — uses green/amber/terracotta which remain distinguishable

**Interaction accessibility:**
- All touch targets minimum 44x44px
- Focus indicators: 2px `primary` outline on all focusable elements (visible in both light and dark modes)
- Tap feedback: subtle background color shift + optional haptic on key actions
- No information conveyed only through animation — all animated content has a static fallback

**Content accessibility:**
- Minimum text size 12px; primary content 16px
- Maximum line width 65 characters
- Sufficient line height (1.4-1.5) for readability
- Screen reader labels on all custom components, icons, and interactive elements
- Semantic heading hierarchy (h1 → h2 → h3) for screen reader navigation

**Motion accessibility:**
- Respect `prefers-reduced-motion` OS setting
- Celebration animations and transitions disabled in reduced motion mode
- No auto-playing animations that can't be paused
- Loading states use static skeleton placeholders when reduced motion is active

## Component Specifications

### Navigation Architecture

**Mobile Navigation — Role-Scoped Bottom Tab Bar:**

| Role | Tab 1 | Tab 2 | Tab 3 | Tab 4 | Tab 5 |
|------|-------|-------|-------|-------|-------|
| **Teacher** | Home (overview + pending) | Grade (camera + queue) | Plan (curriculum) | Messages | More (settings, profile) |
| **Parent** | Dashboard (trend hero) | Progress (per-subject) | Messages | Settings | — |
| **Student** | Growth (trend + tips) | Progress (per-subject) | Tips | Settings | — |

**Tab bar specifications:**
- Height: 56px + safe area inset
- Background: `surface` with `elevation-2` top shadow
- Active tab: `primary` icon (filled variant) + label
- Inactive tab: `text-secondary` icon (outlined) + label
- Labels: `caption` size (12px), always visible (no icon-only tabs)
- Haptic: light tap feedback on tab switch

**Teacher Camera FAB:**
- 56px diameter circle, `primary` background, white camera icon
- Positioned bottom-right, 24px from edges, above tab bar
- Available on all teacher screens (persistent shortcut to grading)
- `elevation-2` shadow
- Press state: slightly darker green + haptic

**Web Navigation — Sidebar:**
- Principal/Admin companion web uses a left sidebar (240px collapsed to 64px)
- Vertical icon + label navigation
- Top: org/school selector
- Bottom: settings, profile, sign out

### Screen Inventory

**Teacher Screens:**

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **Home** | Overview + action center | Pending count card, recent activity feed, quick stats (graded today, avg score) |
| **Grading Queue** | List of assignments pending grading | Assignment cards (subject, class, count), filter by class/subject, sort by date |
| **Camera Capture** | Photo capture for grading | Full-screen camera, alignment guides, shutter button, flash toggle, gallery pick |
| **Grading Review** | AI suggestion review + approval | `GradingCard`: photo thumbnail, suggested score (adjustable), feedback text (editable), confidence badge, rubric breakdown, Approve/Retake/Manual buttons |
| **Batch Grading Progress** | Progress through multiple assignments | Progress bar ("4 of 12"), current `GradingCard`, swipe to skip |
| **Assignment Detail** | View published grade + student history | Score, feedback, submission photo, student trend for this subject |
| **Curriculum Planner** | Lesson and unit planning | Calendar/timeline view, unit cards, AI planning suggestions |
| **Messages** | Contextual messaging threads | Thread list grouped by student, unread badges, search |
| **Message Thread** | Individual conversation | Messages with linked student/assignment context cards, reply composer |
| **Settings** | Preferences and account | Notification preferences, class management, profile, sign out |

**Parent Screens:**

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **Dashboard** | Hero answer: "Is my child improving?" | `TrendIndicator` hero card, subject summary cards, child selector (if multiple) |
| **Subject Detail** | Per-subject longitudinal view | `GrowthTimeline` chart, strengths/weaknesses list, recent assignments |
| **Assignment Detail** | Individual assignment view | Score, teacher feedback, AI explanation, "Message Teacher" action |
| **Messages** | Threads with teachers | Thread list, context-linked messages |
| **Settings** | Notification cadence + account | Digest frequency selector, profile, sign out |

**Student Screens:**

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **Growth Home** | "Where am I growing?" | Overall trend indicator, top 3 improvements, "Next challenge" card |
| **Subject Progress** | Per-subject growth view | `GrowthTimeline` (growth-framed), strengths highlighted, focus areas with tips |
| **Tips** | Actionable improvement suggestions | Tip cards with specific, actionable advice linked to recent performance |
| **Settings** | Basic preferences | Profile, notification settings |

**Principal Screens (Web):**

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **Cohort Dashboard** | School-wide trends | Aggregate trend charts by grade/subject, teacher activity summary |
| **Grade/Subject Drill-down** | Filtered cohort view | Filterable data tables + charts, comparison views |
| **Teacher Overview** | Teacher activity and workload | Grading velocity, feedback quality indicators |

**Admin Screens (Web):**

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **Org Management** | Create/manage organizations | Org list, create org wizard, org settings |
| **User Management** | Manage users and roles | User table with role badges, invite flow, role assignment |
| **School Setup Wizard** | Guided school onboarding | Step-through wizard with progress indicator |

### Core Custom Components

**`TrendIndicator` — The hero answer component:**

```
┌─────────────────────────────────┐
│  ↑  Improving                   │
│  Math · This Month              │
│                                 │
│  "Ava is showing stronger       │
│   computation skills and        │
│   improving in word problems."  │
│                                 │
│  Score trend: 72 → 78 → 85     │
│  [View Details →]               │
└─────────────────────────────────┘
```

| Property | Specification |
|----------|--------------|
| Trend arrow | `hero` size (36px), `success` green (up), `focus` amber (steady), `caution` orange (down). Never red. |
| Subject + timeframe | `body-small`, `text-secondary` |
| Explanation | `body` size, `text-primary`. 1-2 sentences, AI-generated, human-readable. |
| Score trend | `score` font (monospace), showing recent progression |
| Detail link | `body-small`, `primary` color, right-aligned |
| Card | `surface` background, `elevation-1`, `radius-md`, `md` padding |

**`GradingCard` — Teacher review and approval:**

```
┌─────────────────────────────────┐
│ [Photo Thumbnail]    ◐ High     │
│                      Confidence │
│                                 │
│  Suggested Score                │
│  [−]  87 / 100  [+]            │
│                                 │
│  Feedback                       │
│  "Strong understanding of       │
│   fractions. Minor errors in    │
│   Q3 simplification. Review     │
│   reducing to lowest terms."    │
│  [Edit ✎]                       │
│                                 │
│  ┌─ Rubric ──────────────────┐  │
│  │ Accuracy    18/20         │  │
│  │ Method      15/20         │  │
│  │ Completion  20/20         │  │
│  │ Neatness    17/20         │  │
│  │ Explanation 17/20         │  │
│  └───────────────────────────┘  │
│                                 │
│  [Grade Manually]  [Approve ✓]  │
└─────────────────────────────────┘
```

| Property | Specification |
|----------|--------------|
| Photo thumbnail | 80x80px, `radius-sm`, tappable to zoom full-screen |
| Confidence badge | `caption` size. High = `success` green, Medium = `focus` amber, Low = `caution` orange with explanation tooltip |
| Score adjuster | `score` font (32px mono), `−/+` buttons (44px touch targets), or tap number to type directly |
| Feedback text | `body` size, editable on tap (expands to text input with save/cancel) |
| Rubric breakdown | Collapsible section, `body-small`, scores in `score` font |
| Action buttons | "Grade Manually" = outlined secondary, "Approve" = filled `primary` green, both full-width on mobile |
| Card | `surface` background, `elevation-1`, `radius-md`, `md` padding |

**`GrowthTimeline` — Longitudinal progress visualization:**

```
┌─────────────────────────────────┐
│  Math · Last 3 Months           │
│                                 │
│  100 ┤                          │
│   85 ┤            ●─────●      │
│   78 ┤       ●────┘             │
│   72 ┤  ●────┘                  │
│   50 ┤                          │
│      └──┬────┬────┬────┬──     │
│        Jan  Feb  Mar  Apr      │
│                                 │
│  Strengths: Computation, Logic  │
│  Focus: Word Problems           │
│  [View Assignments →]           │
└─────────────────────────────────┘
```

| Property | Specification |
|----------|--------------|
| Chart line | 2px stroke, `primary` color, dots at data points (8px circles) |
| Chart area | Optional subtle gradient fill below line (5% opacity `primary`) |
| Axis labels | `caption` size, `text-secondary` |
| Strengths | `body-small`, `success` green dot prefix |
| Focus areas | `body-small`, `focus` amber dot prefix. Never "weaknesses" — always "Focus" or "Areas for growth" |
| Card | `surface` background, `elevation-1`, `radius-md`, `md` padding |

**`ContextualMessageComposer` — Pre-linked messaging:**

```
┌─────────────────────────────────┐
│  ┌─ Context ─────────────────┐  │
│  │ Re: Ava Chen · Math Quiz  │  │
│  │ Score: 85/100 · Mar 15    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Type your message...      │  │
│  │                           │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                        [Send →] │
└─────────────────────────────────┘
```

| Property | Specification |
|----------|--------------|
| Context card | `surface-dim` background, `radius-sm`, shows student name + assignment + score. Auto-populated, not editable. Dismissible if teacher wants to send without context. |
| Text input | `body` size, multi-line, auto-growing, max 500 characters for MVP |
| Send button | `primary` filled, 44px touch target, disabled until text entered |

**`OnboardingWizard` — Role-specific guided setup:**

| Property | Specification |
|----------|--------------|
| Progress indicator | Horizontal step dots at top. Completed = `primary` filled. Current = `primary` outlined. Future = `text-muted`. |
| Step content | Centered, single-column, generous `2xl` vertical spacing |
| Primary action | Full-width `primary` button at bottom: "Continue," "Get Started," "Finish Setup" |
| Back action | Text button top-left or "Back" link, `text-secondary` |
| Step count | Teacher: 3 steps (profile → classes → first assignment). Parent: 2 steps (sign in → see dashboard). Student: 2 steps (sign in → see growth). Admin: 4 steps (org → school → teachers → confirm). |

### Loading & Empty States

**Loading states (skeleton):**
- Every data-dependent component has a skeleton variant
- Skeletons match the shape and size of real content (not generic rectangles)
- Shimmer animation: left-to-right warm gradient sweep, 1.5s cycle
- Skeleton color: `surface-dim` base, `border` shimmer highlight
- Reduced motion: static `surface-dim` blocks, no shimmer

**Empty states per role:**

| Role | Screen | Empty State Message | Action |
|------|--------|-------------------|--------|
| Teacher | Grading Queue | "All caught up!" | "Snap a Photo" button |
| Teacher | Messages | "No messages yet" | — |
| Parent | Dashboard (no data) | "Waiting for first grades" | — |
| Parent | Messages | "No messages yet" | — |
| Student | Growth | "Your growth journey starts soon" | — |
| Student | Tips | "Tips coming soon" | — |

All empty states use a simple line illustration (single accent color) above the message text. Illustrations are warm and encouraging, not generic clip art.

### Responsive Behavior

| Breakpoint | Width | Layout | Target |
|-----------|-------|--------|--------|
| Mobile | < 768px | Single column, bottom tabs, FAB | Phone (primary) |
| Tablet | 768-1024px | Single column with wider cards, bottom tabs | Tablet |
| Desktop | > 1024px | Sidebar nav + multi-column content area | Web companion |

**Mobile → Web adaptation rules:**
- Tab bar becomes sidebar
- Cards expand to fill wider columns (max-width: 600px per card)
- Data tables gain horizontal scroll or additional visible columns
- Touch targets remain 44px minimum (mouse users benefit too)
- Camera FAB not shown on web (grading is mobile-only in MVP)

## Interaction Patterns

### Core Interaction Flows

**Flow 1: Teacher Grading Loop (Primary Flow)**

```
[Home Screen]
    │
    ├─ Tap "Grade" tab ──→ [Grading Queue]
    │                          │
    │                          ├─ Tap assignment card ──→ [Camera Capture]
    │                          │                              │
    ├─ Tap Camera FAB ────────────────────────────────────────┘
    │                                                         │
    │                                              Snap photo
    │                                                         │
    │                                              ┌──────────▼──────────┐
    │                                              │ Image Quality Check  │
    │                                              │ (client-side, <1s)   │
    │                                              └──────────┬──────────┘
    │                                                    │         │
    │                                                  OK        Blurry
    │                                                    │         │
    │                                                    │    "Photo may be
    │                                                    │     blurry—Retake?"
    │                                                    │     [Retake] [Use Anyway]
    │                                                    │         │
    │                                              ┌─────▼─────────▼─────┐
    │                                              │  AI Processing       │
    │                                              │  (skeleton card,     │
    │                                              │   "Analyzing...")     │
    │                                              └──────────┬──────────┘
    │                                                    │         │
    │                                                Success    Failure
    │                                                    │         │
    │                                              ┌─────▼───┐ ┌──▼──────────┐
    │                                              │ Grading  │ │ Failure Card │
    │                                              │ Card     │ │ [reason]     │
    │                                              │          │ │ [Retake]     │
    │                                              │ Review   │ │ [Manual]     │
    │                                              │ Adjust   │ └─────────────┘
    │                                              │ Approve  │
    │                                              └────┬─────┘
    │                                                   │
    │                                              [Approved ✓]
    │                                              Brief animation
    │                                                   │
    │                                              ┌────▼─────────────┐
    │                                              │ More in batch?    │
    │                                              │ Yes → Next card   │
    │                                              │ No → "All done!"  │
    │                                              └──────────────────┘
```

**Critical timing targets:**
- Camera open: < 500ms from tap
- Image quality check: < 1s (client-side)
- AI processing: < 10s (show progress skeleton immediately)
- Approve to published: < 1s
- Total per-assignment: < 2 minutes including review

**Flow 2: Parent First Visit (Onboarding → Value)**

```
[Invite Link (SMS/Email)]
    │
    ▼
[Sign In with Google]
    │
    ▼
[Child Pre-Linked]──── "Welcome! Ava's dashboard is ready."
    │
    ▼
[Dashboard]
    │
    ├─ Hero: TrendIndicator ── "↑ Ava is improving in Math"
    │
    ├─ Subject cards below ── tap to drill into GrowthTimeline
    │
    └─ [Optional: Set notification preferences]
```

**Critical:** Parent must see their child's trend within 3 taps of receiving the invite link. No manual child-linking, no profile setup forms, no tutorial screens blocking the dashboard.

**Flow 3: Student Growth Check**

```
[Open App]
    │
    ▼
[Growth Home]
    │
    ├─ Overall trend: "You improved in 3 areas this month"
    │
    ├─ Top improvements (celebrating what's working)
    │
    ├─ "Next challenge" card ── actionable tip
    │
    └─ Tap subject ──→ [Subject Progress]
                           │
                           ├─ GrowthTimeline (growth-framed)
                           ├─ Strengths highlighted
                           └─ Focus areas with specific tips
```

**Flow 4: Contextual Messaging**

```
[Any Grade/Assignment Detail Screen]
    │
    Tap "Message Parent" or "Message Teacher"
    │
    ▼
[ContextualMessageComposer]
    │
    ├─ Context auto-linked: Student + Assignment + Score
    │
    ├─ Type message
    │
    └─ Send ──→ Thread created with context card visible to both parties
```

**Flow 5: Admin School Onboarding**

```
[Admin Dashboard]
    │
    Tap "Add School"
    │
    ▼
[OnboardingWizard - 4 steps]
    │
    Step 1: School details (name, address, grade levels)
    │
    Step 2: Invite teachers (email list, bulk or individual)
    │
    Step 3: Configure safety rules (content filters, grade visibility)
    │
    Step 4: Review & confirm
    │
    ▼
["School is live!" ── checklist of what's ready]
    │
    Teachers receive invite emails
```

### Gesture & Input Patterns

**Mobile gestures:**

| Gesture | Context | Action |
|---------|---------|--------|
| **Tap** | Primary interaction everywhere | Select, toggle, navigate, approve |
| **Swipe left** | Grading queue card | Quick actions: skip, archive |
| **Swipe right** | Grading queue card | Quick approve (if previously reviewed) |
| **Pull down** | Any list/dashboard screen | Refresh data |
| **Long press** | Message thread | Copy, reply, view context |
| **Pinch zoom** | Photo in grading review | Zoom into student work |
| **Swipe between** | Batch grading cards | Navigate to next/previous assignment |

**Input patterns:**

| Input | Pattern | Specification |
|-------|---------|--------------|
| **Score entry** | Tap number to type, or use +/− buttons | Number input with min/max validation. +/− buttons are 44px touch targets with haptic feedback. |
| **Feedback editing** | Tap text to enter edit mode | Text area expands inline. Save/Cancel buttons appear. Auto-save after 3s of inactivity as draft. |
| **Search** | Top search bar with filter chips | Debounced search (300ms). Filter chips for class, subject, date range. Results update live. |
| **Date selection** | Native date picker | Platform-native date picker (iOS/Android). No custom calendar widget. |
| **Notification preferences** | Toggle + frequency selector | Toggle per notification type. Frequency: "Instant" / "Daily digest" / "Weekly digest" / "Off". |

### State Management Patterns

**Offline behavior:**

| Action | Offline Behavior | Sync Behavior |
|--------|-----------------|---------------|
| **Photo capture** | Photo saved to local queue with "Pending" badge | Auto-uploads when connected. AI processing begins on server. Push notification when grade is ready for review. |
| **Grade approval** | Queued locally with "Will publish when connected" status | Auto-publishes on reconnect. Parent/student see grade after sync. |
| **Dashboard viewing** | Cached data shown with "Last updated: [timestamp]" banner | Background refresh on reconnect. Skeleton shimmer on stale sections during refresh. |
| **Messaging** | Message queued with "Sending..." status | Auto-sends on reconnect. Timestamp reflects send time, not queue time. |
| **Sign in** | Not possible — requires network | — |

**Optimistic updates:**
- Grade approval: immediately show "Approved" state, roll back if server rejects
- Message send: immediately show in thread, show error if delivery fails
- Notification preference change: immediately reflect new setting

**Data freshness indicators:**
- Dashboard data > 1 hour old: subtle "Last updated 2h ago" text below hero
- Dashboard data > 24 hours old: more prominent "Pull down to refresh" prompt
- Real-time updates via silent push notifications (no polling)

### Error Handling Patterns

**Error hierarchy (most to least severe):**

| Level | Example | UI Treatment |
|-------|---------|-------------|
| **Blocking** | Auth failure, server unreachable for sign-in | Full-screen error with retry button and "Contact support" link |
| **Flow-blocking** | AI processing failure, upload failure | Inline error card within the flow with clear reason + alternative actions (Retake / Grade Manually) |
| **Informational** | Low confidence AI result, stale cached data | Inline badge or banner within the relevant component. Does not block any action. |
| **Silent** | Background sync retry, analytics failure | No user-visible indication. Logged for debugging. |

**Error message format:**
```
[What happened] — plain language, no error codes
[Why it might have happened] — one sentence, helpful not technical
[What to do] — primary action button + optional secondary
```

Example:
```
"Couldn't analyze this photo."
"The handwriting in the bottom section wasn't clear enough."
[Retake Photo]  [Grade Manually]
```

**Never show:**
- Error codes or technical stack traces
- "Something went wrong" without context
- Errors that block the user without offering a forward path

### Notification Patterns

**Notification types by role:**

| Role | Notification | Default Cadence | Configurable? |
|------|-------------|-----------------|---------------|
| **Teacher** | New message from parent | Instant | Yes (instant/digest/off) |
| **Teacher** | AI grading complete (batch) | Instant | Yes |
| **Parent** | New grade published | Weekly digest | Yes (instant/daily/weekly/off) |
| **Parent** | New message from teacher | Instant | Yes |
| **Parent** | Weekly progress summary | Weekly | Yes (weekly/off) |
| **Student** | New growth tip available | Weekly | Yes (weekly/off) |
| **Student** | Progress milestone reached | Instant | No (always instant, low frequency) |
| **Admin** | New teacher accepted invite | Instant | Yes |

**Notification principles:**
- Default to the least intrusive cadence that's still useful
- Parents default to weekly digest — they opt INTO higher frequency, not out of it
- Batch notifications where possible (one digest, not 12 individual grade notifications)
- Every notification deep-links to the relevant screen (not app home)
- Notification preferences are set during onboarding (one screen) and adjustable from settings anytime

### Transition & Animation Specifications

**Screen transitions:**

| Transition | Animation | Duration | Easing |
|-----------|-----------|----------|--------|
| Tab switch | Cross-fade | 200ms | ease-in-out |
| Forward navigation (push) | Slide from right | 250ms | ease-out |
| Back navigation (pop) | Slide to right | 200ms | ease-in |
| Modal/bottom sheet open | Slide up from bottom | 300ms | spring (damping: 0.8) |
| Modal/bottom sheet close | Slide down | 250ms | ease-in |
| Camera open | Fade to camera | 300ms | ease-out |

**Component micro-animations:**

| Component | Animation | Duration | Trigger |
|-----------|-----------|----------|---------|
| Button press | Scale to 0.97 + background shift | 100ms | Touch start |
| Button release | Scale to 1.0 | 150ms | Touch end |
| Grade approve | Checkmark fade-in + card slide to "approved" | 400ms | Tap approve |
| Skeleton shimmer | Left-to-right gradient sweep | 1500ms loop | Loading state |
| Trend arrow | Fade-in + slight upward drift | 300ms | Data loaded |
| Score change | Number cross-fade | 200ms | +/− tap |
| Pull-to-refresh | Spinner rotation | Continuous | Pull gesture |
| Batch progress | Progress bar width transition | 300ms | Grade approved |
| Student milestone | Scale up 1.0→1.05→1.0 + gold shimmer | 600ms | Milestone reached |

**Haptic feedback (iOS/Android):**

| Action | Haptic Type |
|--------|------------|
| Grade approved | Success (medium) |
| Photo captured | Light impact |
| Tab switch | Selection tick |
| Error action | Error (heavy) |
| Student milestone | Success (heavy) |

## Content Strategy

### Voice & Tone

**Brand voice:** Clear, warm, competent. Teacher OS speaks like a trusted colleague — knowledgeable but never condescending, supportive but never patronizing.

**Voice principles:**

| Principle | Do | Don't |
|-----------|-----|-------|
| **Direct** | "12 assignments to review" | "You have some assignments that may need your attention" |
| **Warm** | "Ava is improving in Math this month" | "Student #4521 performance metric: +8%" |
| **Confident** | "Suggested score: 87" | "The AI thinks this might possibly be around 87" |
| **Honest** | "Couldn't analyze this photo — handwriting was unclear" | "Something went wrong. Please try again" |
| **Empowering** | "Your call — adjust if needed" | "AI has determined the final score" |

**Tone adaptation by context:**

| Context | Tone | Example |
|---------|------|---------|
| **Grading flow** | Efficient, minimal | "Suggested: 87/100" — no extra words |
| **Parent dashboard** | Reassuring, clear | "Ava is showing stronger computation skills this month" |
| **Student growth** | Encouraging, specific | "You improved in 3 areas — nice work on fractions!" |
| **Error states** | Calm, helpful | "Photo was too blurry to read. Retake or grade manually." |
| **Onboarding** | Welcoming, guiding | "Welcome! Let's get your first class set up." |
| **Empty states** | Friendly, action-oriented | "No grades yet. Snap a photo to start grading." |
| **Notifications** | Brief, actionable | "Weekly summary: Ava improved in Math, steady in Reading." |
| **Admin/system** | Functional, precise | "3 teachers invited. 1 accepted. 2 pending." |

### Role-Specific Language

**Teacher-facing language:**

| Instead of | Use | Why |
|-----------|-----|-----|
| "AI-graded" | "Suggested score" | Teacher retains authority |
| "Submit for processing" | "Snap" or "Capture" | Faster mental model |
| "Override AI" | "Adjust" | Not a conflict — it's normal |
| "Final grade" | "Approved grade" | Teacher approved it, AI didn't decide it |
| "Automated feedback" | "Draft feedback" | Teacher can edit, it's a starting point |
| "Error" | Specific reason | "Handwriting unclear in Q3" not "Processing error" |

**Parent-facing language:**

| Instead of | Use | Why |
|-----------|-----|-----|
| "Performance metrics" | "How [child name] is doing" | Human, not clinical |
| "Below average" | "Area for focus" or "Room to grow" | Growth framing |
| "Score: 72/100" | "72 out of 100 — [context sentence]" | Number alone is anxiety-inducing |
| "Data unavailable" | "Grades will appear here once posted" | Explains why, not just what |
| "Notification settings" | "How often would you like updates?" | Question, not jargon |
| "Dashboard" | "Your child's progress" | Plain language |

**Student-facing language:**

| Instead of | Use | Why |
|-----------|-----|-----|
| "Your grade" | "Your score" or "How you did" | Less weight, less judgment |
| "Weakness" | "Next challenge" or "Focus area" | Agency, not deficit |
| "Below average" | "Room to grow" | Never comparative to peers |
| "You failed" | Never used | Not in the vocabulary |
| "Try harder" | "Here's a tip that might help" | Specific and actionable |
| "Report" | "Your growth" | Ownership language |
| "Good job" | "You improved by 8 points — that's real progress" | Specific praise, not generic |

### Content Patterns

**Trend explanations (AI-generated, parent-facing):**

Format: `[Child name] is [trend direction] in [subject] [timeframe]. [One specific observation]. [One actionable insight or reassurance].`

Examples:
- "Ava is improving in Math this month. Her computation accuracy has gone up consistently. Word problems are still a focus area — practicing at home with real-world examples can help."
- "Ava is steady in Reading this quarter. Comprehension is strong and consistent. Vocabulary is an area where a little extra practice could make a difference."
- "Ava needs some extra support in Science this month. Her scores on the last two quizzes were lower than usual. This is common when new topics are introduced — it often improves with practice."

**Rules for trend explanations:**
- Always use the child's name, never "your child" or "the student"
- Always name the specific strength or focus area — never vague
- Downward trends: normalize ("this is common"), suggest action, never alarm
- Never compare to class average or other students
- Maximum 3 sentences

**AI grading feedback (teacher-facing, editable):**

Format: `[Overall assessment — 1 sentence]. [Specific strength]. [Specific area for improvement with detail].`

Example:
- "Strong understanding of fraction operations. Clear work shown for addition and multiplication problems. Q3: simplification stopped at 4/8 — review reducing to lowest terms."

**Rules for AI feedback:**
- Factual, specific, referencing actual content in the photo
- No value judgments ("good student," "poor effort")
- Improvement areas reference specific questions/sections
- Teacher can edit freely — this is a draft, not a verdict

**Student tips (actionable improvement suggestions):**

Format: `[What to try] — [Why it helps] — [How long it takes]`

Examples:
- "Practice simplifying fractions by finding the largest number that divides both top and bottom. This builds the habit so it becomes automatic. Try 5 problems tonight — should take about 10 minutes."
- "Before answering a word problem, underline the question it's actually asking. This helps avoid solving the wrong thing. Try it on your next homework."

**Rules for student tips:**
- One specific, actionable thing — not a study plan
- Include estimated effort ("10 minutes," "try it on your next homework")
- Linked to their actual recent performance, not generic advice
- Encouraging tone — "try this" not "you need to fix this"

### Microcopy Inventory

**Buttons & Actions:**

| Action | Label | Note |
|--------|-------|------|
| Take photo | "Snap" | One word, camera-native |
| Submit AI grading | Automatic — no button | Happens on capture |
| Approve grade | "Approve" | Clear, authoritative |
| Approve and continue | "Approve & Next" | Batch grading flow |
| Edit feedback | "Edit" (with pencil icon) | Inline action |
| Retake photo | "Retake" | Simple, no blame |
| Grade without AI | "Grade Manually" | Clear alternative |
| Send message | "Send" | Standard |
| View details | "View Details" or "→" | Consistent drill-down pattern |
| Sign in | "Sign in with Google" | Match Google branding guidelines |
| Set up class | "Add Class" | Action-oriented |
| Invite teachers | "Invite Teachers" | Clear who's being invited |

**Status Labels:**

| State | Label | Color |
|-------|-------|-------|
| AI processing | "Analyzing..." | `text-secondary` |
| Awaiting review | "Ready for Review" | `focus` amber |
| Approved | "Approved" | `success` green |
| Published | "Published" | `success` green |
| Offline queued | "Will send when connected" | `text-secondary` |
| Invite pending | "Invite Sent" | `focus` amber |
| Invite accepted | "Active" | `success` green |

**Empty State Messages:**

| Screen | Headline | Supporting Text | Action |
|--------|----------|----------------|--------|
| Teacher grading queue | "All caught up!" | "No assignments waiting for review." | "Snap a Photo" button |
| Teacher messages | "No messages yet" | "You can message any parent from a grade detail." | — |
| Parent dashboard (no data) | "Waiting for first grades" | "Grades will appear here once [teacher name] posts them. You'll get a notification." | — |
| Parent messages | "No messages yet" | "You can reach your child's teacher from any assignment." | — |
| Student growth (no data) | "Your growth journey starts soon" | "Once your teacher posts grades, you'll see how you're improving here." | — |
| Student tips | "Tips coming soon" | "After your first few grades, you'll get personalized tips here." | — |

**Confirmation Messages:**

| Action | Confirmation | Duration |
|--------|-------------|----------|
| Grade approved | "Approved ✓" (inline on card) | Persists as state change |
| Batch complete | "All done! 12 assignments graded in 18 minutes." | Screen until dismissed |
| Message sent | "Sent ✓" (inline) | 2s toast, then thread updates |
| School created | "School is live! ✓" + readiness checklist | Screen until dismissed |
| Settings saved | "Saved" (inline near changed setting) | 2s fade |

**Error Messages:**

| Error | Message | Actions |
|-------|---------|---------|
| Blurry photo (pre-AI) | "Photo may be blurry. Retake for better results?" | [Retake] [Use Anyway] |
| AI processing failure | "Couldn't analyze this photo. [Specific reason]." | [Retake Photo] [Grade Manually] |
| Low confidence AI | "AI is less certain about this one — please review carefully." | Badge on GradingCard, no blocking action |
| Upload failure (offline) | "No connection. Photo saved — will upload when you're back online." | — (auto-resolves) |
| Upload failure (server) | "Upload failed. Tap to retry." | [Retry] |
| Sign-in failure | "Couldn't sign in. Check your connection and try again." | [Try Again] |
| Permission denied | "You don't have access to this. Contact your school admin." | — |

## Accessibility Requirements

### WCAG 2.1 AA Compliance

Teacher OS targets **WCAG 2.1 Level AA** compliance across all surfaces. This is both an ethical commitment and a practical necessity — educators, parents, and students span a wide range of abilities, ages, devices, and contexts.

### Visual Accessibility

**Color contrast:**

| Element | Minimum Ratio | Validation |
|---------|--------------|------------|
| Body text on backgrounds | 4.5:1 | All `text-primary` / `surface` and `text-primary` / `background` combinations validated |
| Large text (≥18px bold, ≥24px regular) | 3:1 | All heading combinations validated |
| UI components (icons, borders, inputs) | 3:1 | All interactive element boundaries validated |
| Disabled states | No minimum (intentionally low contrast) | But always paired with additional indicator (opacity change, strikethrough, or label) |

**Color independence:**
- Never rely on color alone to convey meaning
- Trend indicators: arrow direction + color + text label ("↑ Improving" not just green arrow)
- Confidence badges: icon + color + text ("◐ Medium Confidence" not just amber dot)
- Growth timeline: data point shapes vary if multiple lines (circle, square, diamond) in addition to color
- Error states: icon + color + text message
- Success states: checkmark icon + color + text confirmation

**Text scaling:**
- Support dynamic type / system font scaling up to 200%
- Layouts reflow gracefully at larger text sizes — no truncation of critical content
- Minimum text size: 12px at default scale (never smaller)
- Test at 100%, 150%, and 200% scale for all screens

**Dark mode:**
- Full dark mode support via Tamagui theme switching
- All contrast ratios validated independently for dark mode palette
- No pure white (#FFFFFF) text on dark backgrounds — use warm off-white (#F0EDE6)
- Images and illustrations adapt or have dark-mode variants where needed

### Motor Accessibility

**Touch targets:**

| Element | Minimum Size | Spacing |
|---------|-------------|---------|
| Buttons | 44 × 44px | 8px between adjacent targets |
| Tab bar items | 44 × 56px (full tab height) | No gap (full-width distribution) |
| Score +/− buttons | 44 × 44px | 16px from score number |
| List items (tappable) | Full width × 48px minimum height | 1px divider or 8px gap |
| Camera shutter | 64 × 64px | Centered, generous margin |
| FAB | 56 × 56px | 24px from edges |

**Gesture alternatives:**
- Every swipe action has a tap alternative (swipe to skip → tap menu → "Skip")
- Pinch-to-zoom on photos also available via double-tap zoom
- Pull-to-refresh also available via "Refresh" button in overflow menu
- No gesture-only actions — all core functionality accessible via taps

**One-handed operation:**
- Primary actions in bottom third of screen (thumb zone)
- Tab bar at bottom
- Approve button at bottom of GradingCard
- Camera shutter at bottom center
- Back navigation via bottom-left gesture or top-left button (both supported)

### Screen Reader Support

**Semantic structure:**
- All screens use proper heading hierarchy (h1 → h2 → h3)
- Lists use semantic list elements (not styled divs)
- Tables use semantic table elements with headers
- Navigation uses nav landmarks
- Main content area uses main landmark

**Component labeling:**

| Component | Accessible Label | Announcement |
|-----------|-----------------|--------------|
| TrendIndicator | "Math trend: improving. Ava is showing stronger computation skills this month." | Full context in single announcement |
| GradingCard | "Grading: [student name], [assignment name]. Suggested score: 87 out of 100. High confidence." | Key info first, details on explore |
| Score adjuster | "Score: 87. Adjustable. Use plus and minus buttons or double-tap to enter a number." | Current value + interaction hint |
| Confidence badge | "AI confidence: high" / "AI confidence: low — handwriting unclear in section 3" | Includes reason for low confidence |
| GrowthTimeline chart | "Math progress over 3 months. Scores: January 72, February 78, March 85. Trend: improving." | Data table fallback for chart content |
| Camera FAB | "Open camera to grade an assignment" | Clear action description |
| Empty states | Full message read as single announcement | Includes action hint if available |

**Focus management:**
- Modal open: focus moves to modal title or first interactive element
- Modal close: focus returns to trigger element
- Screen navigation: focus moves to screen title (h1)
- Error appearance: focus moves to error message
- Grade approved: announcement "Grade approved for [student name]" then focus moves to next card or completion message
- Batch grading: after approval, focus moves to next GradingCard automatically

**Live regions:**
- AI processing status ("Analyzing...") announced as polite live region
- Score changes on +/− tap announced as assertive live region ("Score: 88")
- Notification toasts announced as polite live region
- Error messages announced as assertive live region

### Cognitive Accessibility

**Information architecture:**
- Maximum 5 tabs per role (Miller's Law — chunking)
- Maximum 3 levels of navigation depth from any screen
- Consistent placement of primary actions (always bottom of screen)
- Consistent back navigation (always top-left)

**Reading level:**
- All system-generated text (UI labels, empty states, error messages): Grade 6 reading level or below
- AI-generated parent explanations: Grade 8 reading level or below
- AI-generated student tips: Grade 5 reading level or below
- No jargon, no abbreviations without first use expansion
- Short sentences (max 20 words per sentence for system text)

**Cognitive load reduction:**
- One primary action per screen — never two competing calls to action
- Progressive disclosure — details hidden until requested
- Consistent patterns — same interactions work the same way everywhere
- Status persistence — user always knows where they are (active tab highlighted, breadcrumbs on web)
- Undo where possible — approved grade can be unapproved within a window

**Memory aids:**
- Search available on all list screens (teacher queue, messages, admin users)
- Recent activity visible on home screens
- Filter states persist across sessions (teacher's last-used class filter remembered)
- Unread/new badges on items requiring attention

### Motion & Vestibular

**Reduced motion support:**
- Respect `prefers-reduced-motion` OS setting globally
- When active:
  - All transitions become instant (0ms duration)
  - Skeleton shimmer becomes static gray blocks
  - Celebration animations disabled (checkmark appears without animation)
  - Trend arrows appear without drift animation
  - Score changes appear without cross-fade
  - Pull-to-refresh uses static indicator instead of spinner
- No auto-playing animations anywhere in the app (even with motion enabled)
- No parallax effects
- No infinite scrolling animations (content loads, scroll is native)

### Internationalization Readiness

**MVP scope:** English only. But the design system is built for future i18n:

- All user-facing strings externalized (no hardcoded text in components)
- Layouts accommodate 40% text expansion (German, Finnish tend to be longer)
- RTL-aware layout using Tamagui's built-in RTL support (flexDirection reversal, margin/padding mirroring)
- Date/time/number formatting via Intl API (locale-aware)
- No text embedded in images or icons
- Icon meanings don't rely on cultural assumptions (no thumbs-up as universal "good," etc.)

### Testing Requirements

| Test Type | Frequency | Tools |
|-----------|-----------|-------|
| Automated contrast checking | Every build (CI) | axe-core, jest-axe |
| Screen reader testing | Every sprint | VoiceOver (iOS), TalkBack (Android) |
| Keyboard navigation (web) | Every sprint | Manual testing |
| Dynamic type testing | Every sprint | iOS/Android accessibility settings |
| Reduced motion testing | Every sprint | OS accessibility settings |
| WCAG audit | Quarterly | Manual audit against WCAG 2.1 AA checklist |
| User testing with assistive tech users | Pre-launch + annually | Recruited participants |
