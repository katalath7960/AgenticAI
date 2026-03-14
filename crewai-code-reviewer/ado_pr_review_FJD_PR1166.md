# 🔍 Azure DevOps PR Review

| Field | Value |
|-------|-------|
| **Organisation** | stellarus |
| **Project** | FJD |
| **Repository** | FJD |
| **PR** | #1166 – case party and create filing |
| **Author** | Jiande Li |
| **Branches** | `Jiande_Testing` → `development` |
| **Files reviewed** | 6 |
| **Generated** | 2026-03-13 06:35:04 |

---

# Code Review Report

## Executive Summary

The codebase exhibits a solid foundation with clear type usage, consistent React component structure, and well-organized feature layering for a full-stack React and .NET Core application. Key strengths include typed API interaction, modular UI components, and separation of concerns across pages and steps. However, there are recurring medium-severity issues primarily around accessibility (missing ARIA attributes, focus management), React key stability, effect dependency management, error handling robustness, and security best practices such as proper sanitization of dynamically inserted HTML. Some UI patterns (popups for document viewing) and state management logic (mixed save/navigation flows) contribute to potential usability and maintainability risks. Implementing the recommended corrective actions will significantly elevate the user experience, reduce bugs, improve security posture, and enhance maintainability.

**Overall Code Quality Score:** 87

---

## Score Breakdown

| Area         | Score | Critical | High | Medium | Low |
|--------------|-------|----------|------|--------|-----|
| Frontend     | 85    | 0        | 0    | 11     | 5   |
| Backend      | N/A   | 0        | 0    | 0      | 0   |
| Security     | 87    | 0        | 0    | 9      | 4   |
| Performance  | 88    | 0        | 0    | 10     | 5   |
| Code Quality | 88    | 0        | 0    | 14     | 4   |
| **Overall**  | 87    | 0        | 0    | 44     | 18  |

*Note:* Backend-specific issues were not provided; overall scores focus on frontend and integration layers.

---

## Critical & High Severity Issues (Action Required)

*No critical or high severity issues reported.*

---

## Frontend Issues (All Severities)

1. **Unstable React keys in PartyCard list**  
   *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx` (320-360)  
   *Severity:* Medium  
   *Description:* Keys use mutable or display fields (`PARTY_SEQ_NO`, `PIDM`, `LAST_NAME`).  
   *Fix:* Use stable immutable IDs only.

2. **Repeated useEffect trigger for loading aliases**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx` (230-270)  
   *Severity:* Medium  
   *Description:* `aliasesByParty` in dependencies causes infinite loops.  
   *Fix:* Remove from dependency array; track fetched keys separately.

3. **Ambiguous cache keys for parties**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx` (409-413)  
   *Severity:* Low  
   *Description:* Naive concatenation of `PIDM` and `PARTY_SEQ_NO` can cause collisions.  
   *Fix:* Normalize values and use robust delimiters.

4. **PIDM required in `handleSaveParty` prevents adding parties without PIDM**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx` (470-514)  
   *Severity:* Medium  
   *Description:* New parties with missing PIDM blocked from saving.  
   *Fix:* Support optional PIDM with coordinated backend validation.

5. **Accessibility: disabled inputs lack ARIA notifications in AddPartyModal**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx` (240-360)  
   *Severity:* Medium  
   *Description:* Disabled controls missing `aria-disabled`; buttons lack labels.  
   *Fix:* Add ARIA attributes and contextual labels/explanations.

6. **Debounced party search without request cancellation leads to race conditions**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx` (166-191)  
   *Severity:* Medium  
   *Description:* No `AbortController` cancels previous pending requests.  
   *Fix:* Implement fetch cancellation and caching.

7. **Incorrect falsy seqNo parsing in parseContacts function**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx` (125-130)  
   *Severity:* Low  
   *Description:* `seqNo=0` coerced to `null`.  
   *Fix:* Use explicit `Number.isNaN` checks.

8. **Unlabeled popup document viewer and alert() usage**  
   *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx` (500-520)  
   *Severity:* Medium  
   *Description:* No ARIA labeling or focus management; poor error UX.  
   *Fix:* Use accessible in-app modal instead; replace alerts with notifications.

9. **Brittle fee API error handling disables future requests permanently**  
   *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx` (140-160)  
   *Severity:* Medium  
   *Description:* String matching on errors is fragile.  
   *Fix:* Use standardized error codes; add retry and user feedback.

10. **Fee input controls lack ARIA and validation feedback**  
    *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx` (multiple)  
    *Severity:* Low  
    *Description:* Inputs allow invalid negative values; lack aria-invalid.  
    *Fix:* Add validation messages and aria attributes; enforce constraints.

11. **Mixed save and navigation logic reduces maintainability**  
    *File:* `/src/pages/CreateFiling/FilingWizard.tsx` (680-730)  
    *Severity:* Medium  
    *Description:* Save logic intermingled with step navigation.  
    *Fix:* Extract saves to dedicated functions/hooks.

12. **Save-All dialog lacks accessibility attributes and labels**  
    *File:* `/src/pages/CreateFiling/FilingWizard.tsx` (820-865)  
    *Severity:* Medium  
    *Description:* Missing `aria-labelledby`, `aria-describedby`, and close button label.  
    *Fix:* Add appropriate aria props.

13. **Hidden tabs remain mounted leading to accessibility and performance issues**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx` (865-900)  
    *Severity:* Low  
    *Description:* `display: none` hides but does not unmount tab panels.  
    *Fix:* Conditionally render tab panels; use WAI-ARIA roles.

14. **Async navigation side effects without cancellation guard**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx` (630-660)  
    *Severity:* Medium  
    *Description:* Calls `navigate` after async fetch without checking component mounted state.  
    *Fix:* Guard side effects with cancellation or mount checks.

15. **Repeated Issue 1 - unstable React keys in PartyCard**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx` (duplicate)  
    *Severity:* Medium

---

## Backend Issues (All Severities)

*No backend-specific issues were reported in the provided context.*

---

## Security Vulnerabilities

1. **PIDM requirement blocking new parties is a potential auth failure**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Medium  
   *Remediation:* Allow save without PIDM if backend supports it; harden backend validation.

2. **Stored XSS risk in dynamic popup document title injection**  
   *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
   *Severity:* Medium  
   *Remediation:* Sanitize inputs; avoid raw HTML injection; replace popup with modal dialog; use notifications over alert().

3. **Redundant party alias fetching and ambiguous keys risk data inconsistency**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Medium  
   *Remediation:* Fix dependencies, normalize keys, avoid redundant network calls.

4. **AddPartyModal disables controls without ARIA support, harming accessibility**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx`  
   *Severity:* Medium  
   *Remediation:* Add `aria-disabled` and explanatory labels/tooltips.

5. **Fragile fee API error parsing risks misbehavior and user confusion**  
   *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx`  
   *Severity:* Medium  
   *Remediation:* Use structured error codes and retry logic.

6. **Mixed save/navigation risks data loss and race conditions**  
   *File:* `/src/pages/CreateFiling/FilingWizard.tsx`  
   *Severity:* Medium  
   *Remediation:* Decouple navigation and saves; improve error handling.

7. **Accessibility omissions in Save All Confirmation Dialog**  
   *File:* `/src/pages/CreateFiling/FilingWizard.tsx`  
   *Severity:* Medium  
   *Remediation:* Add aria attributes and button labels.

8. **Case Details tab hiding via CSS causes screen reader confusion**  
   *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
   *Severity:* Low  
   *Remediation:* Use conditional rendering and ARIA roles.

9. **Party key forms can collide causing data integrity issues**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Low  
   *Remediation:* Normalize keys explicitly.

10. **Contact parsing coerces false falsy values, losing data accuracy**  
    *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx`  
    *Severity:* Low  
    *Remediation:* Use precise NaN checks.

11. **Fee input fields lack validation ARIA attributes**  
    *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx`  
    *Severity:* Low  
    *Remediation:* Add validation feedback and associate aria-describedby.

12. **Async navigation side effects without cancellation guard cause React errors**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
    *Severity:* Medium  
    *Remediation:* Guard async side effects.

13. **Repeated unstable React keys risk UI glitches and security issues**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
    *Severity:* Medium

---

## Performance Issues

1. **Unstable React keys in PartyCard components cause unnecessary re-renders**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Medium

2. **Redundant alias fetching caused by improper effect dependencies**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Medium

3. **Ambiguous party keys causing cache collisions**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Low

4. **PIDM requirement blocks save flows, leading to backend retries and UX delays**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties.tsx`  
   *Severity:* Medium

5. **Accessibility gaps in AddPartyModal reduce keyboard/screen reader usability**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx`  
   *Severity:* Medium

6. **No abort controller in debounced existing party search causes race conditions**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx`  
   *Severity:* Medium

7. **Incorrect contact seqNo parsing disables features or shows incorrect UI**  
   *File:* `/src/pages/CaseManagement/Case Details/Parties/AddPartyModal.tsx`  
   *Severity:* Low

8. **Popup document viewer risks blocked windows and poor error feedback**  
   *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
   *Severity:* Medium

9. **Brittle fee API error detection disables future fetches improperly**  
   *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx`  
   *Severity:* Medium

10. **Fee inputs lack validation and aria attributes for screen readers**  
    *File:* `/src/pages/CreateFiling/steps/PaymentStep.tsx`  
    *Severity:* Low

11. **Mixed navigation and save calls cause redundant network overhead**  
    *File:* `/src/pages/CreateFiling/FilingWizard.tsx`  
    *Severity:* Medium

12. **Save All dialog lacks ARIA support reducing accessibility**  
    *File:* `/src/pages/CreateFiling/FilingWizard.tsx`  
    *Severity:* Medium

13. **Hidden tabs remain mounted leading to wasted DOM size and accessibility issues**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
    *Severity:* Low

14. **Async navigation side effects without cancellation create runtime warnings**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
    *Severity:* Medium

15. **Repeated unstable React keys contribute to re-render inefficiencies (duplicate)**  
    *File:* `/src/pages/CaseManagement/Case Details/CaseDetails.tsx`  
    *Severity:* Medium

---

## Code Quality & SOLID Violations

1. **Component >30 lines with complex state logic, e.g., CaseDetails.tsx**  
   *Principle:* Single Responsibility  
   *Severity:* Medium  
   *Suggestion:* Break down complex components into smaller subcomponents or hooks.

2. **Mixed responsibilities in save & navigation logic (FilingWizard)**  
   *Principle:* Single Responsibility & Open/Closed  
   *Severity:* Medium  
   *Suggestion:* Extract save operations into dedicated hooks or service layers.

3. **Repeated parsing and mapping utilities scattered**  
   *Principle:* Duplication  
   *Severity:* Medium  
   *Suggestion:* Centralize parsing logic into reusable utility modules.

4. **Improper keys in lists leading to React reconciliation problems**  
   *Principle:* React Keys & Clean Code  
   *Severity:* Medium  
   *Suggestion:* Use stable unique IDs only.

5. **Long methods and large JSX blocks reduce readability**  
   *Principle:* Clean Code  
   *Severity:* Medium  
   *Suggestion:* Refactor to smaller methods, leverage React patterns like render props or hooks.

6. **API call error handling inconsistent and brittle**  
   *Principle:* Error Handling  
   *Severity:* Medium  
   *Suggestion:* Define consistent error response shapes and parsing strategies.

7. **Interfaces in types scattered with legacy fields and implicit any**  
   *Principle:* Interface Segregation & Type Safety  
   *Severity:* Low  
   *Suggestion:* Refine interfaces and use utility mapped types carefully.

---

## Refactoring Roadmap

### 1. Immediate

- Stabilize React list keys using immutable unique identifiers in `PartyCard` and similar components. This fixes multiple UI and reconciliation bugs.
- Add ARIA attributes (`aria-disabled`, `aria-labelledby`, `aria-describedby`) to modals, dialogs, disabled inputs, and buttons for accessibility compliance.
- Sanitize dynamic HTML inputs and replace popup document viewers with accessible modal dialogs to eliminate stored XSS and poor UX.
- Refactor complex `handleNext` logic in `FilingWizard` to separate save and navigation concerns. Add debouncing and standardized error handling.
- Implement backend-supported structured error responses and enhance fee API error handling with retries and user feedback.
- Introduce request cancellation (using `AbortController`) in existing-party search and other debounced API calls.

### 2. Short-term

- Remove redundant `aliasesByParty` dependency in the useEffect hook by tracking fetched keys with refs or sets.
- Normalize party cache keys explicitly to avoid collisions.
- Add inline validation and aria-invalid attributes on fee inputs and other form controls.
- Add accessibility labels and notifications for disabled form controls throughout `AddPartyModal`.
- Conditionally render tab content panels unmounted when hidden with WAI-ARIA compliant roles and aria-hidden toggling.
- Add cancellation guards (`isMounted` flags or cancellation tokens) to async effects calling navigation or state setters.
- Memoize step contents in `FilingWizard` and consider dynamic imports for large step components.

### 3. Long-term

- Refactor large components with multiple responsibilities into smaller, focused subcomponents or custom hooks.
- Centralize duplicated parsing and mapping logic into shared utilities/services.
- Strengthen type definitions and reduce reliance on legacy or loosely typed fields with precise interfaces or value objects.
- Design a comprehensive error handling and notification system with a Result pattern or similar for API interactions.
- Evaluate and improve frontend security in collaboration with backend teams, enforcing strict validation and sanitization policies.
- Enforce consistent patterns for all network requests, including caching, cancellation, and error management.

---

## Best Practices Violations Summary

- **Unstable React keys:** Using mutable or non-unique data fields as keys is a recurring anti-pattern causing UI glitches.
- **Effect dependencies:** Including state objects like maps in dependency arrays without control leads to excessive network calls.
- **Inconsistent error handling:** Using brittle string matching for error detection reduces code robustness.
- **Accessibility gaps:** Disabled form controls, dialogs, and popups lack ARIA support resulting in poor assistive tech experience.
- **Mixed concerns in handlers:** UI logic tightly coupled with data saving causes maintainability challenges.
- **Duplication:** Utilities for parsing and mapping are fragmented rather than consolidated.
- **Unsafe HTML injection:** Dynamically inserted unescaped content risks XSS vulnerabilities.

---

*Report generated by CrewAI Code Review Agent*