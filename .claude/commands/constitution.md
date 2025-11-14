---
name: Constitution
description: Create and manage project governance principles, development guidelines, and foundational rules that guide all technical decisions.
category: Spec-Kit
tags: [spec-kit, constitution, governance, principles]
---

**Purpose**
Create principles focused on code quality, testing standards, user consistency, and performance requirements. These principles will govern how technical decisions and implementation choices are made throughout the project.

**When to Use**
- At the start of a new project to establish core principles
- When project direction needs clear governance
- Before making significant architectural decisions
- To ensure consistency across AI agent implementations

**What It Creates**
- `.specify/memory/constitution.md` - Core project principles
- Governance rules for technical decisions
- Quality standards and guidelines
- Implementation constraints and preferences

**Workflow Position**
1. **`/constitution`** - Establish project principles
2. **`/specify`** - Define what to build
3. **`/plan`** - Create technical implementation plan
4. **`/tasks`** - Generate executable task list
5. **`/implement`** - Execute all tasks

**Example**
```bash
/constitution Create principles for a Python-based quantitative trading system that emphasizes:
- Code quality with 80% test coverage requirement
- Performance-critical path optimization
- Risk management and safety-first approach
- Clear separation of concerns between data, strategy, and execution
- Comprehensive logging and monitoring for production systems
```

**Notes**
- The constitution will be referenced by AI agents during specification, planning, and implementation phases
- Keep principles focused and actionable
- Each principle should have clear evaluation criteria