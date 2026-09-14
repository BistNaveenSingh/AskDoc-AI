<!-- GSD:project-start source:PROJECT.md -->

## Project

**AskDoc AI — AI-Powered Document Question Answering System**

A Retrieval-Augmented Generation (RAG) application that lets users upload PDF documents (policies, manuals, reports) and ask natural-language questions about them. The system retrieves relevant passages, generates answers grounded only in document content with source citations, and explicitly says "I don't know" when the answer isn't in the documents. Built as a learning-first project to deeply understand RAG pipelines end to end.

**Core Value:** **Users get accurate, source-cited answers from their documents — never hallucinated content.** If the answer isn't in the documents, the system says so.

### Constraints

- **LLM Provider**: OpenAI only for v1 — GPT-4o-mini for generation, text-embedding-3-small for embeddings. Keeps the stack simple and cost low (~$0.15/M input tokens)
- **Vector Store**: FAISS (local, in-memory/on-disk) — no external vector DB setup required
- **No secrets in code**: All API keys via `.env` file, `.env.example` committed as reference
- **Modularity**: Separate files for ingestion, chunking, embeddings, retrieval, generation, API — never one monolithic script
- **Learning-first**: Every file and function must include explanatory comments; code clarity over cleverness

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
