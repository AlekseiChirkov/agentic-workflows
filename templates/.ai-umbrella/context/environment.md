# environment.md — shared environment configuration

## Purpose
Environment topology and shared infrastructure identifiers used across services.
Service-specific values (port numbers, DB connection strings) go in the service's
own .ai/context/environment.md.

## Structure

## Environments
One subsection per environment (dev, staging, prod): shared URLs, GCP project IDs,
cluster names, Kubernetes namespaces, region.

## Shared Configuration
Values all services need: auth domain, event bus topic prefix, service mesh settings,
shared secret names in Secret Manager.
