# Documentation Map

This map links current product decisions, implementation boundaries, release criteria, and setup instructions.

## 1. Core Project Docs
- [README.md](README.md): Product entry point and development quick start.
- [PRODUCT.md](PRODUCT.md): High-level vision, value proposition, and feature list.
- [ARCHITECTURE.md](ARCHITECTURE.md): High-level architecture, component breakdown, and data flow.
- [STRUCTURE.md](STRUCTURE.md): Proposed repository layout and technology stack.
- [SETUP.md](SETUP.md): Roles and workflow for Codex and Antigravity.

## 2. Technical Specifications
- [SPEC/DATABASE.md](SPEC/DATABASE.md): SQLite schema, indexing strategy, and vector storage implementation.
- [SPEC/AI_PIPELINE.md](SPEC/AI_PIPELINE.md): Agent reasoning, provider boundary, urgency ranking, and schedule validation.
- [SPEC/INTEGRATIONS.md](SPEC/INTEGRATIONS.md): Specifications for the pluggable data ingestion system.
- [SPEC/API_CONTRACT.md](SPEC/API_CONTRACT.md): API definitions between the Tauri shell and FastAPI backend.
- [SPEC/INTEGRATIONS.md](SPEC/INTEGRATIONS.md): Connector contract, Google scopes, data flow, and credential policy.
- [SPEC/RELEASE_ACCEPTANCE.md](SPEC/RELEASE_ACCEPTANCE.md): Testable MVP acceptance criteria and release phases.

## 3. Development Guides
- [GUIDES/SETUP.md](GUIDES/SETUP.md): Step-by-step setup guide for Rust, Python, Node.js, and pnpm.
- [GUIDES/CONTRIBUTING.md](GUIDES/CONTRIBUTING.md): Guidelines for adding context integrations.
- [GUIDES/DEPLOYMENT.md](GUIDES/DEPLOYMENT.md): Instructions for building the Tauri desktop product and evaluation demo.

## 4. Project Management
- [ROADMAP.md](ROADMAP.md): Proposed MVP → Beta → v1.0 phases; no release dates set.
- [TODO.md](TODO.md): Current implementation status and prioritized next work.
