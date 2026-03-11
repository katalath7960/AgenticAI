# 🔍 Azure DevOps PR Review

| Field | Value |
|-------|-------|
| **Organisation** | stellarus |
| **Project** | FJD |
| **Repository** | FJD |
| **PR** | #1149 – My In-Progress pagination bug fix and user filing load |
| **Author** | Richard Li |
| **Branches** | `Richard-DEV` → `development` |
| **Files reviewed** | 1 |
| **Generated** | 2026-03-09 16:52:47 |

---

# Code Review Report

## Executive Summary
The reviewed codebase centers on a complex React frontend component integrating a MUI Data Grid with multiple asynchronous data sources, Redux state, and client-server communication via API calls. The codebase shows generally good structure with proper use of React hooks, TypeScript typings, and Redux integration, but suffers from large component size and mixing of concerns beyond a single responsibility. Several medium-severity issues affect maintainability, performance, and user experience. A critical security concern arises from client-side construction of raw SQL-like filter strings, exposing the system to injection risks if backend protections are insufficient. Other security issues around access control assumptions, token storage, navigation data exposure, and logging are present but less severe. Performance bottlenecks include redundant network calls due to unstable dependencies and unnecessary re-renders caused by inline function props. Accessibility can be improved by clarifying UI semantics and adding aria-labels. Overall, the code represents a solid foundation but requires urgent remediation of security critical points alongside progressive architectural refinements and improved error handling.

**Overall Code Quality Score: 83**

---

## Score Breakdown

| Area         | Score | Critical | High | Medium | Low  |
|--------------|-------|----------|------|--------|------|
| Frontend     | 82    | 0        | 1    | 5      | 4    |
| Backend      | N/A   | N/A      | N/A  | N/A    | N/A  |
| Security     | 87    | 0        | 1    | 4      | 5    |
| Performance  | 87    | 0        | 1    | 5      | 4    |
| Code Quality | 80    | 0        | 1    | 6      | 3    |
| **Overall**  | 83    | 0        | 1    | 5      | 4    |

> **Note:** Backend analysis was not provided; scores reflect frontend and cross-cutting layers only.

---

## Critical & High Severity Issues (Action Required)

### Security
- **High:** SQL Injection risk from client-side raw SQL filter string construction (`escapeSQL` usage) allowing untrusted input concatenation.
  
### Frontend
- **High:** Same SQL injection risk reflected as frontend anti-pattern (`escapeSQL`), also endangering maintainability and correctness.

### Performance
- **High:** Redundant API calls caused by unstable dependencies in hook fetching reference data (`filingTypes` dependency in `fetchFilingCategories`), adding latency.

### Code Quality
- **High:** Client-side raw SQL-like filter construction with manual escaping creating brittle, insecure, and hard-to-maintain code.

---

## Frontend Issues (All Severities)

1. **Component Structure | State | Medium**  
   `handleRowClick` mixes navigation logic with event handling, duplicates complex state payloads, and uses unsafe type assertions.

2. **Performance | Hooks | State | Medium**  
   `fetchFilingCategories` depends on `filingTypes` leading to repeated fetch cycles and re-renders.

3. **Error Handling | Hooks | Medium**  
   `fetchData` suppresses errors silently without UI feedback or retry options.

4. **UI / a11y | Low**  
   `Emergency` column renderCell uses inverted null/undefined checks; lacks aria-labels.

5. **Performance | Hooks | Low**  
   Custom filter operators `useMemo` without dependencies risks stale closures.

6. **Performance | Anti-Pattern | Medium**  
   Inline anonymous functions passed to `MUIDataGrid` cause avoidable re-renders.

7. **Performance | Low**  
   Imports from `@mui/x-data-grid-premium` alongside custom wrapper may inflate bundle size.

8. **Security | Anti-Patterns | High**  
   Client escapes SQL strings manually - security risk and anti-pattern.

9. **State | Code Cleanliness | Low**  
   Vestigial or unused state variables (`queueid`, `configLoaded`) confuse maintainers.

10. **Hooks | Performance | Medium**  
    Effect dependencies use multiple large arrays replaced on each load, causing excessive re-renders.

---

## Backend Issues (All Severities)

_No backend code or findings were provided for review._

---

## Security Vulnerabilities

1. **High**  
   Client-side raw SQL-like filter string construction with manual escaping exposing SQL Injection risk (OWASP A03:2021).

2. **Medium**  
   Reliance on client-side filtering of `ASSIGNEDTO` username; backend authorization may be insufficient (A01:2021).

3. **Medium**  
   Possible XSS risk rendering untrusted text data without explicit sanitization (A03:2021).

4. **Medium**  
   Potential token exposure due to unclear client storage (A02:2021).

5. **Medium**  
   Sensitive data passed via navigation state risking unintended exposure (A07:2021).

6. **Info**  
   Use of large/third-party components (MUI) requires monitoring for vulnerabilities (A06:2021).

7. **Low**  
   Potential unvalidated forwards or open redirect risk via row navigation query parameters (A10:2021).

8. **Low**  
   Accessibility mis-signaling in Emergency column renderCell (A04/A05:2021).

9. **Low**  
   Console logs exposing sensitive information (A09:2021).

10. **Low**  
    Lack of retry or error UI on fetch failures affects usability/security (A05:2021).

---

## Performance Issues

1. **Medium**  
   Mixing navigation logic and large state passing in `handleRowClick` harms performance and memory.

2. **Medium**  
   `fetchFilingCategories` re-fetches triggered excessively by unstable `filingTypes` dependency.

3. **Medium**  
   Silent failed fetches degrade UX and delay problem discovery.

4. **Low**  
   Inverted emergency logic and missing aria-labels reduce UX quality.

5. **Low**  
   Static filter operator `useMemo` lacks dependencies risking stale computations.

6. **Medium**  
   Inline function props to `MUIDataGrid` provoke unnecessary grid re-renders.

7. **Low**  
   Potentially bloated bundle size due to duplicate or broad imports.

8. **High**  
   Client-side raw SQL-like filter construction risks heavy backend load or exploits.

9. **Low**  
   Vestigial state variables add cognitive and execution overhead.

10. **Medium**  
    Dependencies on new array objects cause extra repeated API calls and renders.

---

## Code Quality & SOLID Violations

1. **Medium | SOLID-Single Responsibility**  
   `MyInProgressPage` component is too large and handles multiple concerns—data fetching, UI logic, navigation—within a single component.

2. **Medium | Clean Code**  
   `fetchFilingCategories` callback depends on unstable external state causing multiple recreations and potential refresh loops.

3. **Medium | Error Handling**  
   Fetch functions suppress errors silently, violating fail-fast and transparency principles.

4. **Low | Accessibility & Clean Code**  
   Emergency column render logic is opaque and lacks accessibility features.

5. **Low | Performance**  
   Use of `useMemo` without dependencies for custom operators could cause stale closures.

6. **Medium | Performance / Clean Code**  
   Inline anonymous callbacks inside MUIDataGrid props lead to avoidable re-renders.

7. **Low | Architecture / Performance**  
   Excessive and possibly duplicated third-party imports leading to bundle size growth.

8. **High | Security / Clean Code**  
   Raw SQL string construction with manual escaping is fragile, insecure, and tightly couples filter logic to query syntax.

9. **Low | Clean Code**  
   Unused or vestigial state variables reduce clarity and can mislead maintainers.

10. **Medium | Hooks / Performance**  
    Effect hook dependencies on multiple new array references cause repeated data fetching and rendering.

---

## Refactoring Roadmap

### 1. Immediate (Critical / High Issues)

- **Eliminate client-side raw SQL filter string construction and `escapeSQL` usage.**  
  Refactor filter parameters to structured format (e.g., JSON objects), enforce backend parameterized queries. This is the most urgent security fix to prevent SQL injection.

- **Add user-visible error feedback and retry mechanisms for all data fetching flows.**  
  Replace silent errors with UI alerts/toasts and retry logic to improve UX and resilience.

- **Apply strict backend authorization and input validation.**  
  Ensure backend enforces user permissions robustly; do not rely solely on frontend filtering.

### 2. Short-term (Medium Issues & Performance Wins)

- **Break down the `MyInProgressPage` component into smaller focused parts.**  
  Extract data fetching hooks, column config, and navigation logic for better maintainability and testability.

- **Consolidate related reference data fetching to avoid re-fetch thrashing.**  
  Fetch filing types and categories together in single effect or via global store/context with memoized selectors.

- **Memoize all handler callbacks passed to MUI Data Grid using `useCallback`.**  
  To prevent unnecessary re-renders and improve performance.

- **Remove or annotate unused/vintage state variables like `queueid` and `configLoaded`.**

- **Clarify Emergency column render logic and add accessibility labels (aria-label).**

- **Stabilize effect dependencies with memoization or selector to avoid redundant refreshing.**

### 3. Long-term (Architectural Improvements, Tech Debt)

- **Introduce centralized state management or context providers for reference data and caching.**

- **Migrate to modern data-fetching libraries (React Query, SWR) for better caching, deduplication, and stale data handling.**

- **Implement server-side pagination and filtering via APIs with strict contract interfaces instead of client-side SQL fragments.**

- **Audit third-party libraries regularly to maintain minimum attack surface and bundle size.**

- **Improve accessibility comprehensively, adding keyboard navigation, ARIA landmarks, and screen reader announcements.**

- **Add comprehensive unit and integration tests for navigation, data fetching, and UI components to ensure reliability.**

---

## Best Practices Violations Summary

- **Large component god-class** managing too many responsibilities violates Single Responsibility Principle.

- **Client-side raw SQL string construction** increases security and maintenance risks.

- **Inline anonymous functions passed as props** increase rendering cost and complexity.

- **Insufficient error handling and user feedback** creates fragile user experiences.

- **Unstable dependencies in hooks causing excessive fetches and re-renders.**

- **Inconsistent or unclear accessibility practices**, missing ARIA attributes on interactive/status UI elements.

- **Logging of potentially sensitive data directly to console in production.**

- **Heavy and redundant imports from UI libraries increasing bundle size unnecessarily.**

---

*Report generated by CrewAI Code Review Agent*