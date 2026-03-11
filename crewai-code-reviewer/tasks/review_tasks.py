"""
Review Tasks
=============
Task definitions for each review agent in the code review crew.
"""

from crewai import Task, Agent


def create_frontend_review_task(agent: Agent, context: dict) -> Task:
    """Create the frontend code review task."""
    return Task(
        description=f"""
You are reviewing a React frontend codebase. Analyze every file below and
produce a structured list of findings.

## File Tree
{context['file_tree']}

## Frontend Code
{context['frontend_code']}

## Review Checklist
For each file, evaluate:

1. **Component Structure** – Are components small, focused, and composable?
   Do they follow the single-responsibility principle?
2. **Hooks Usage** – Are hooks (useState, useEffect, useCallback, useMemo,
   useRef, custom hooks) used correctly? Are dependency arrays accurate?
   Are there missing cleanup functions?
3. **State Management** – Is state lifted appropriately? Is there prop
   drilling that should be replaced with context or a state library?
   Is derived state computed correctly?
4. **Anti-Patterns** – Look for: setState inside render, direct DOM
   manipulation, index-as-key on dynamic lists, nested ternaries,
   business logic in components, circular dependencies.
5. **Accessibility (a11y)** – Are ARIA attributes used correctly? Do
   interactive elements have labels? Is keyboard navigation supported?
   Are colour contrast and focus indicators adequate?
6. **Performance** – Unnecessary re-renders, missing memoization, large
   bundle imports, synchronous heavy computation on the main thread,
   missing code splitting, unoptimized images.
7. **TypeScript** – Are types accurate and specific (no `any`)? Are
   interfaces/types exported and reused? Are generics used where helpful?
8. **Error Handling** – Are error boundaries present? Are async errors
   caught? Is user-facing error feedback provided?

## Output Format
Return your findings as structured Markdown using this exact template
(repeat the Issue block for every finding):

### Frontend Review Findings

#### Issue 1
- **File:** `<filename>`
- **Line (approx):** <line or range>
- **Category:** <Component Structure | Hooks | State | Anti-Pattern | a11y | Performance | TypeScript | Error Handling>
- **Severity:** <Critical | High | Medium | Low | Info>
- **Description:** <clear explanation>
- **Recommended Fix:** <concrete code suggestion or guidance>

...repeat for each issue...

#### Summary
- Total issues: <N>
- Critical: <N> | High: <N> | Medium: <N> | Low: <N> | Info: <N>
- Frontend Quality Score: <0-100>
""",
        expected_output=(
            "A structured Markdown report of all frontend issues found, "
            "categorized by type and severity, with recommended fixes and "
            "a quality score."
        ),
        agent=agent,
    )


def create_backend_review_task(agent: Agent, context: dict) -> Task:
    """Create the backend code review task."""
    return Task(
        description=f"""
You are reviewing a .NET Core Web API backend codebase. Analyze every file
below and produce a structured list of findings.

## File Tree
{context['file_tree']}

## Backend Code
{context['backend_code']}

## Review Checklist
For each file, evaluate:

1. **Controller Design** – Are controllers thin? Do they delegate to
   services? Are route attributes, HTTP verbs, and model binding correct?
   Is ActionResult<T> used consistently?
2. **Service Architecture** – Is business logic in services, not
   controllers? Are interfaces defined for every service? Is the service
   layer testable in isolation?
3. **Dependency Injection** – Are lifetimes (Transient, Scoped, Singleton)
   correct? Are there captive dependency issues? Is IServiceProvider
   resolved at startup or abused at runtime?
4. **Async/Await** – Are I/O-bound calls awaited? Is `.Result` or
   `.Wait()` used (sync-over-async)? Are CancellationTokens propagated?
   Are async methods suffixed with `Async`?
5. **Error Handling** – Are exceptions caught at the right level? Is
   there a global exception handler / middleware? Are domain exceptions
   distinguished from infrastructure exceptions? Are ProblemDetails
   returned for errors?
6. **Logging** – Is structured logging used (ILogger<T>)? Are log levels
   appropriate? Is sensitive data excluded from logs?
7. **API Design & REST** – Are endpoints RESTful? Are HTTP status codes
   correct? Is versioning present? Are DTOs used instead of exposing
   domain models?
8. **Middleware** – Is middleware ordered correctly? Are cross-cutting
   concerns (auth, CORS, rate limiting) handled via middleware?
9. **Entity Framework / Data Access** – Are queries efficient? Is
   tracking disabled for read-only queries? Are migrations clean?

## Output Format
Return your findings as structured Markdown:

### Backend Review Findings

#### Issue 1
- **File:** `<filename>`
- **Line (approx):** <line or range>
- **Category:** <Controller | Service | DI | Async | Error Handling | Logging | API Design | Middleware | Data Access>
- **Severity:** <Critical | High | Medium | Low | Info>
- **Description:** <clear explanation>
- **Recommended Fix:** <concrete code suggestion or guidance>

...repeat for each issue...

#### Summary
- Total issues: <N>
- Critical: <N> | High: <N> | Medium: <N> | Low: <N> | Info: <N>
- Backend Quality Score: <0-100>
""",
        expected_output=(
            "A structured Markdown report of all backend issues found, "
            "categorized by type and severity, with recommended fixes and "
            "a quality score."
        ),
        agent=agent,
    )


def create_security_review_task(agent: Agent, context: dict) -> Task:
    """Create the security review task."""
    return Task(
        description=f"""
You are performing a security audit of a full-stack application with a React
frontend and .NET Core Web API backend. Analyze all code below.

## File Tree
{context['file_tree']}

## All Code
{context['all_code']}

## Security Review Checklist

### Frontend Security
1. **XSS** – Is `dangerouslySetInnerHTML` used? Is user input sanitized
   before rendering? Are URL parameters reflected unsafely?
2. **Sensitive Data Exposure** – Are API keys, tokens, or secrets in
   client-side code? Are they in environment variables correctly?
3. **Auth Token Handling** – Are JWTs stored in HttpOnly cookies (not
   localStorage)? Is token refresh handled securely?
4. **CSRF** – Are anti-CSRF tokens used for state-changing requests?
5. **Third-party Dependencies** – Are there known-vulnerable packages?

### Backend Security
1. **Injection** – SQL injection, command injection, LDAP injection.
   Is parameterized data access used everywhere?
2. **Authentication & Authorization** – Are endpoints protected with
   [Authorize]? Are roles/policies configured correctly? Is the auth
   middleware in the right order?
3. **Input Validation** – Are all inputs validated (model validation,
   FluentValidation, etc.)? Are file uploads restricted?
4. **CORS** – Is CORS configured restrictively? Are wildcard origins
   avoided in production?
5. **Secrets Management** – Are connection strings, API keys, etc.
   stored in environment variables or a vault, not in code?
6. **HTTP Security Headers** – HSTS, X-Content-Type-Options,
   X-Frame-Options, CSP?
7. **Rate Limiting** – Is rate limiting in place for auth endpoints?
8. **Logging Sensitive Data** – Are passwords, tokens, PII excluded
   from logs?
9. **OWASP Top-10** – Cover each of the OWASP Top-10 2021 categories.

## Output Format

### Security Review Findings

#### Vulnerability 1
- **File:** `<filename>`
- **Layer:** <Frontend | Backend | Both>
- **OWASP Category:** <e.g., A03:2021 - Injection>
- **Severity:** <Critical | High | Medium | Low | Info>
- **Description:** <what the vulnerability is>
- **Attack Scenario:** <how it could be exploited>
- **Remediation:** <specific fix>

...repeat for each vulnerability...

#### Summary
- Total vulnerabilities: <N>
- Critical: <N> | High: <N> | Medium: <N> | Low: <N> | Info: <N>
- Security Score: <0-100> (100 = no issues found)
""",
        expected_output=(
            "A structured Markdown report of all security vulnerabilities "
            "found, categorized by OWASP category and severity, with "
            "attack scenarios and remediation steps."
        ),
        agent=agent,
    )


def create_performance_review_task(agent: Agent, context: dict) -> Task:
    """Create the performance review task."""
    return Task(
        description=f"""
You are performing a performance review of a full-stack application with a
React frontend and .NET Core Web API backend.

## File Tree
{context['file_tree']}

## All Code
{context['all_code']}

## Performance Review Checklist

### Frontend Performance
1. **Render Optimization** – Unnecessary re-renders, missing React.memo,
   missing useMemo/useCallback, expensive computations in render.
2. **Bundle Size** – Large imports that could be tree-shaken, missing
   dynamic imports / code splitting, unused dependencies.
3. **Network** – Redundant API calls, missing request deduplication,
   missing caching (React Query/SWR stale-while-revalidate).
4. **Images & Assets** – Unoptimized images, missing lazy loading,
   missing responsive images (srcset).
5. **List Rendering** – Large lists without virtualization, missing keys,
   O(n²) operations in render loops.

### Backend Performance
1. **Database Queries** – N+1 queries, missing eager loading, unindexed
   columns in WHERE/JOIN clauses, loading unnecessary columns (SELECT *).
2. **Async Pipeline** – Blocking calls, missing ConfigureAwait(false)
   in library code, thread-pool starvation risks.
3. **Caching** – Missing caching for expensive or rarely-changing data,
   missing HTTP caching headers (ETag, Cache-Control).
4. **Serialization** – Inefficient JSON serialization, missing
   System.Text.Json source generators.
5. **Memory** – Large object allocations, string concatenation in loops,
   missing IAsyncEnumerable for streaming, IDisposable not disposed.
6. **API Response** – Over-fetching (returning too much data), missing
   pagination, missing compression.

## Output Format

### Performance Review Findings

#### Issue 1
- **File:** `<filename>`
- **Layer:** <Frontend | Backend>
- **Category:** <Render | Bundle | Network | Database | Async | Caching | Memory | API Response>
- **Severity:** <Critical | High | Medium | Low | Info>
- **Estimated Impact:** <e.g., "~200ms added latency per request">
- **Description:** <clear explanation>
- **Recommended Fix:** <concrete optimization>

...repeat for each issue...

#### Summary
- Total issues: <N>
- Critical: <N> | High: <N> | Medium: <N> | Low: <N> | Info: <N>
- Performance Score: <0-100>
""",
        expected_output=(
            "A structured Markdown report of all performance issues found, "
            "categorized by type, layer, and severity, with estimated impact "
            "and optimization recommendations."
        ),
        agent=agent,
    )


def create_quality_audit_task(agent: Agent, context: dict) -> Task:
    """Create the code quality audit task."""
    return Task(
        description=f"""
You are auditing the overall code quality of a full-stack application with
a React frontend and .NET Core Web API backend.

## File Tree
{context['file_tree']}

## All Code
{context['all_code']}

## Code Quality Checklist

1. **SOLID Principles**
   - Single Responsibility – Does each class/component have one reason to
     change?
   - Open/Closed – Can behaviour be extended without modifying existing code?
   - Liskov Substitution – Are subtypes substitutable for their base types?
   - Interface Segregation – Are interfaces focused and minimal?
   - Dependency Inversion – Do high-level modules depend on abstractions?

2. **Clean Code**
   - Are functions/methods short (<30 lines) and focused?
   - Are names descriptive and consistent?
   - Are magic numbers replaced with named constants?
   - Is there dead code or commented-out code?

3. **Code Duplication**
   - Identify duplicated or near-duplicate logic across files.
   - Suggest shared utilities, hooks, or base classes.

4. **Architecture Patterns**
   - Is the project organized by feature or layer?
   - Are cross-cutting concerns separated?
   - Is the dependency graph clean (no circular dependencies)?

5. **Naming Conventions**
   - React: PascalCase components, camelCase functions/variables,
     UPPER_SNAKE_CASE constants.
   - C#: PascalCase types/methods, camelCase locals, _camelCase private
     fields, I-prefix interfaces.

6. **Error Handling Patterns**
   - Are errors handled consistently?
   - Is the Result pattern used where appropriate?

7. **Testability Indicators**
   - Are there test files? Is the code structured to be testable?

## Output Format

### Code Quality Audit Findings

#### Finding 1
- **File(s):** `<filename(s)>`
- **Principle:** <SOLID-S | SOLID-O | SOLID-L | SOLID-I | SOLID-D | Clean Code | Duplication | Architecture | Naming | Error Handling | Testability>
- **Severity:** <Critical | High | Medium | Low | Info>
- **Description:** <clear explanation>
- **Refactoring Suggestion:** <concrete recommendation>

...repeat for each finding...

#### Overall Code Quality Score: <0-100>
Breakdown:
- Maintainability: <0-100>
- Readability: <0-100>
- Architecture: <0-100>
- Consistency: <0-100>
- Testability: <0-100>

#### Top 5 Refactoring Priorities
1. ...
2. ...
3. ...
4. ...
5. ...
""",
        expected_output=(
            "A structured Markdown report with a code quality score, "
            "detailed findings by principle, and a prioritized list of "
            "refactoring recommendations."
        ),
        agent=agent,
    )


def create_aggregation_task(agent: Agent, context: dict) -> Task:
    """Create the final aggregation task that combines all reviews."""
    return Task(
        description="""
You are the lead reviewer responsible for combining all individual review
reports into a single, cohesive final report.

Using the findings from all previous review tasks in this crew, produce
the definitive code review report. You MUST include every section below.

## Final Report Structure

# Code Review Report

## Executive Summary
- One-paragraph overview of the codebase health.
- Overall Code Quality Score: <0-100> (weighted average of all area scores)

## Score Breakdown
| Area         | Score | Critical | High | Medium | Low |
|--------------|-------|----------|------|--------|-----|
| Frontend     |       |          |      |        |     |
| Backend      |       |          |      |        |     |
| Security     |       |          |      |        |     |
| Performance  |       |          |      |        |     |
| Code Quality |       |          |      |        |     |
| **Overall**  |       |          |      |        |     |

## Critical & High Severity Issues (Action Required)
List every Critical and High issue from all reviews, grouped by area.

## Frontend Issues (All Severities)
Full list from the frontend review.

## Backend Issues (All Severities)
Full list from the backend review.

## Security Vulnerabilities
Full list from the security review.

## Performance Issues
Full list from the performance review.

## Code Quality & SOLID Violations
Full list from the quality audit.

## Refactoring Roadmap
Prioritized list of improvements organized into:
1. **Immediate** (Critical/High issues, security vulnerabilities)
2. **Short-term** (Medium issues, performance wins)
3. **Long-term** (Architectural improvements, tech debt)

## Best Practices Violations Summary
A consolidated list of recurring patterns that violate best practices.

---
*Report generated by CrewAI Code Review Agent*
""",
        expected_output=(
            "A single, comprehensive Markdown report that aggregates all "
            "individual review findings into the prescribed structure with "
            "scores, issue tables, and a prioritized refactoring roadmap."
        ),
        agent=agent,
    )
