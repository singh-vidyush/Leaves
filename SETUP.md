# Tooling Setup & Role Definition

To maximize productivity, this project utilizes both **Codex** and the **Antigravity CLI**. They are used in complementary but distinct roles to avoid overlap and reduce cognitive load.

## 1. Codex: The Architect & Reviewer
**Role**: High-level intelligence, strategic planning, and quality assurance.

**Primary Tasks**:
- **Architecture Design**: Defining the HLD, API contracts, and database schemas.
- **Workspace Management**: Organizing the repository and managing the project's "memory" via `.codex/`.
- **Complex Refactoring**: Analyzing large blocks of code for architectural flaws and proposing structural changes.
- **Code Review**: Auditing changes made by Antigravity to ensure they align with the project's vision and security standards.
- **Documentation**: Writing and updating the `.md` files in `/docs`.

**When to use Codex**: When you need to think "Why" or "How" (e.g., *"How should we implement the vector search to ensure privacy?"*).

## 2. Antigravity: The Builder & Executor
**Role**: Rapid iteration, boilerplate generation, and routine implementation.

**Primary Tasks**:
- **Boilerplate Generation**: Scaffolding new FastAPI endpoints, React components, or Rust modules.
- **Feature Implementation**: Writing the actual logic for a specific task once the design is approved.
- **Script Execution**: Running setup scripts, build commands, and tests.
- **Routine Updates**: Fixing small bugs, updating dependencies, or adding simple UI elements.
- **Rapid Prototyping**: Quickly trying out a library or API before formalizing the implementation.

**When to use Antigravity**: When you know exactly "What" needs to be done (e.g., *"Create a React hook that fetches the latest memories from /api/memories"*).

## Workflow Example
1. **Codex**: Defines the API contract for the Memory Service in `SPEC/API_CONTRACT.md`.
2. **Antigravity**: Implements the FastAPI endpoints and the corresponding React frontend calls.
3. **Codex**: Reviews the implementation and suggests optimizations for data privacy.
4. **Antigravity**: Applies the suggested optimizations.
