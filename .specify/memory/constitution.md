# CODEX Quant Trading System Constitution

## Core Principles

### I. Engineering Bottom Line First (铁律)
Define engineering fundamentals and constraints before discussing technology stack. No technology decisions without clear requirements, success metrics, and acceptance criteria. Every technical choice must have documented rationale tied to project objectives.

**Rationale**: Prevents "future promise" complexity and ensures every line of code serves a clear purpose.

### II. Clarify Before Plan (先Clarify，再Plan)
Before any implementation planning, use /speckit.clarify to identify and resolve all ambiguities. Document all assumptions, dependencies, and open questions before design phase begins.

**Rationale**: Converting "rework" to "problem definition" is critical for team collaboration and reduces downstream complexity.

### III. Research as Executable Memo (研究当可执行备忘录)
Create research.md files as executable task lists when version/dependency uncertainties arise. Use Agent to systematically resolve technical uncertainties. Never let "fuzzy stack" enter implementation phase.

**Rationale**: Structured research approach prevents technical debt from ambiguous decisions.

### IV. Test-Driven Development (NON-NEGOTIABLE)
TDD mandatory for all production code: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. No exceptions for prototypes or "quick fixes."

**Rationale**: Spec Kit's hardest guardrail ensures quality and prevents regressions.

### V. Integration Testing Priority
Integration tests required for: New library contracts, Contract changes, Inter-service communication, Shared schemas. Unit tests alone insufficient for multi-service validation.

**Rationale**: Catch integration issues early before they cascade through system.

### VI. Simplicity Over Complexity
Start simple, follow YAGNI principles. If a simpler alternative exists that meets requirements, choose it. Complexity must be justified with concrete evidence of necessity.

**Rationale**: Maintains system maintainability and reduces cognitive load.

### VII. Sub-Agent Accelerated Development
Use specialized agents proactively for complex tasks: code-reviewer, frontend-developer, rust-pro, ml-engineer, security-auditor. Match agent capabilities to task domain.

**Rationale**: Accelerates development while maintaining code quality through domain expertise.

### VIII. Performance Through Measurement
All performance optimizations must be evidence-based with before/after benchmarks. Set measurable targets: 10x Rust improvement, <100ms latency, >95% uptime. Monitor continuously.

**Rationale**: Performance without measurement is premature optimization.

## Additional Constraints

### Technology Stack
- **Core Languages**: Python 3.13+ (primary), Rust 1.91+ (performance-critical)
- **Backtesting**: QF-Lib 4.0.4 with PythonBacktestEngine fallback
- **Frontend**: React-based with TypeScript
- **Database**: PostgreSQL with Redis caching
- **Message Queue**: Asyncio-based for event processing

### Performance Standards
- Backtest execution: <10 seconds for 1000-day strategy
- Real-time data latency: <100ms end-to-end
- System uptime during trading hours: >95%
- Rust core calculations: 10x faster than Python equivalent
- Frontend load time: <2 seconds for all pages

### Quality Gates
- All code must pass TypeScript/Python type checking
- Test coverage: >80% for core modules, >60% for utilities
- Documentation: All public APIs must have docstrings and examples
- Security: All financial data encrypted at rest and in transit
- Compliance: All backtest results must be reproducible with random seed

## Development Workflow

### Phase Gates
1. **Specification Gate**: All user stories must have independent testability
2. **Architecture Gate**: Constitution check must pass before any planning
3. **Design Gate**: All contracts and data models must be finalized before implementation
4. **Implementation Gate**: All tests must pass before merge
5. **Verification Gate**: Independent validation of all success criteria

### Review Process
- All PRs must verify constitution compliance
- Complexity justification required for any violations
- Performance benchmarks required for optimization PRs
- Security review required for data access changes

### Quality Gates
- Continuous integration must pass all tests
- Backtest validation against historical data
- Paper trading validation before live trading
- Code review required for all commits to main branch

## Governance

**Constitution Supersedes**: This constitution supersedes all other development practices unless explicitly overridden by documented exception.

**Amendment Process**:
1. Proposed change documented with rationale
2. Impact analysis on existing codebase
3. Team review and approval
4. Migration plan for existing code
5. Version bump following semantic versioning rules

**Compliance Review**:
- All PRs/reviews must verify constitution compliance
- Architecture decisions must reference specific principles
- Complexity must be justified with concrete evidence
- Use /analyze before implementation to catch conflicts

**Versioning Policy**:
- MAJOR: Backward incompatible governance changes or principle removals
- MINOR: New principles or materially expanded guidance
- PATCH: Clarifications, typo fixes, non-semantic refinements

**Violation Consequences**:
- Critical violations: PR blocked until resolved
- Major violations: Require explicit approval with documented justification
- Minor violations: Warning logged for retrospective analysis

**Version**: 1.0.0 | **Ratified**: 2025-11-12 | **Last Amended**: 2025-11-12
