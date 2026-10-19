# architecture.md — system topology

## Purpose
Describes how all services in this system fit together: service boundaries,
communication patterns, shared infrastructure. Updated when a cross-cutting
architectural decision (in adr/) materially changes the system shape.
Answers "what is the shape of this system today?"

Individual service architectures live in each service's .ai/memory/architecture.md.

## Structure

## Overview
One paragraph: what the system does and how the major services interact.

## Services
One subsection per service: responsibility, public contract (API/events), key dependencies
on other services. Link to service repo.

## Communication Patterns
How services communicate: sync (HTTP/gRPC), async (events/queues), shared storage.
Include sequence diagrams for critical flows if helpful.

## Shared Infrastructure
Databases, queues, caches, auth systems shared across services.

## External Dependencies
Third-party services and APIs used by multiple parts of the system.
