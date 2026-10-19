# coding.md — shared coding standards

## Purpose
Default coding standards for all services. When a service uses a different stack
(e.g., Go instead of Python), its own .ai/principles/coding.md overrides the
relevant sections and states what it inherits vs replaces.

## Structure

## Default Stack
<!-- Language, framework, DB driver, test tooling used unless overridden at service level.
     Example: Python 3.12, FastAPI, SQLAlchemy 2 async, pytest -->

## Standards

### Types and Contracts
<!-- Type hint requirements, DTO patterns, validation library (e.g., Pydantic v2) -->

### Error Handling
<!-- Exception strategy, logging library (e.g., structlog), forbidden patterns -->

### Testing
<!-- TDD sequence, what to mock vs what to keep real, naming convention -->

### Naming Conventions
<!-- File names, functions, booleans, abbreviation rules -->

## Forbidden — All Services
<!-- Non-negotiable prohibitions: hardcoded secrets, print() in production code, etc. -->
