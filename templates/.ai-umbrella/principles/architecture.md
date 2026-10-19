# architecture.md — shared architectural principles

## Purpose
Principles all services in this system must follow. These are non-negotiable
cross-cutting constraints. Service-specific principles go in the service's own
.ai/principles/architecture.md as extensions or narrow overrides with explicit rationale.

## Structure

## Principles

### Service Boundaries
<!-- How services divide responsibilities; what may and may not cross a boundary.
     Example: services own their data — no shared databases across service boundaries. -->

### Communication Contract
<!-- How services communicate: sync vs async, versioning, backward compatibility rules. -->

### Layer Boundaries
<!-- Shared layer rules that apply to every service: api/, application/, domain/, infrastructure/ -->

### Data Ownership
<!-- Which service owns which entities; rules for cross-service data access. -->

### Observability
<!-- Shared tracing, logging, and metrics standards all services must implement. -->
