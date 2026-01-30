---
description: FastAPI architecture and coding standards
applyTo: '**/*.py'
---

# FastAPI Architecture & Coding Standards

You are an expert Python Backend Engineer and Software Architect. When generating code for this FastAPI project, adhere to the following architectural patterns and standards.

## 1. Project Structure & Layering
- **Strict Separation of Concerns**: Maintain a clear boundary between the API layer (routes), Service layer (business logic), and Data layer (models/schemas).
- **Thin Routes**: Controllers in `app/api/` should only handle HTTP concerns (status codes, dependency injection, routing).
- **Service Layer**: All business logic, third-party integrations, and complex data manipulation must reside in `app/services/`.
- **Schemas**: Use Pydantic v2 models in `app/schemas/` for all request/response validation. Use `model_validate` and `model_dump`.

## 2. Pythonic Standards & Modern Syntax
- **Python 3.10+**: Use modern type hinting. Prefer `list[str]` over `List[str]` and `str | None` over `Optional[str]`.
- **Asynchronous Patterns**: Use `async def` for endpoints and I/O-bound service methods. Utilize `anyio` or `asyncio` appropriately.
- **Dependency Injection**: Use FastAPI's `Depends` for database sessions, authentication, and shared logic. Avoid global state.
- **Pydantic v2**: Utilize `model_validate`, `model_dump`, and `Field` for all schemas.

## 3. API Design
- **Versioning**: Always nest routers under versioned prefixes (e.g., `/api/v1`).
- **Response Models**: Explicitly define `response_model` in route decorators to ensure data filtering and documentation accuracy.
- **Error Handling**: Raise `fastapi.HTTPException` within the service or API layer. Use custom exception handlers for domain-specific errors.

## 4. Documentation & Configuration
- **Pydantic Settings**: Manage all environment variables using `pydantic-settings`.
- **Docstrings**: Provide Google-style docstrings for complex service methods.
- **Typing**: Every function signature must have complete type hints for arguments and return values.
- **OpenAPI**: Provide clear `summary`, `description`, and `response_model` for every route to ensure high-quality Swagger/Redoc output.

## 5. Performance & Security
- **Lifespan**: Use the `lifespan` context manager for startup and shutdown logic (e.g., DB connection pooling).
- **Security**: Implement OAuth2 with Bearer tokens where applicable, keeping security logic in `app/core/security.py`.

## 6. Split-Identity Security Model
- **User Authentication**: Use Google Identity Platform for end-users. Implement a FastAPI dependency that validates Google JWTs (checking `iss`, `aud`, and `exp`).
- **Workload Identity**: Use Azure Entra ID for pod-level access to cloud resources. Utilize `azure.identity.aio.DefaultAzureCredential`.
- **Auth Boundary**: User identity (Google) is for Application Authorization. Workload identity (Azure) is for Infrastructure access. Never mix these contexts.

## 7. Kubernetes & Cloud-Native Patterns
- **Probes**: Implement a `/healthz` or `/health` router that checks critical dependencies (DB, Redis) for readiness and liveness.
- **Observability**: Use OpenTelemetry (OTEL) for instrumentation. Ensure tracers are injected into the service layer to track request flow across microservices.
- **Graceful Shutdown**: Utilize the `lifespan` event to close database pools and finish processing background tasks before the SIGTERM from K8s takes effect.

## 8. Configuration & Infrastructure
- **Terraform Integration**: Ensure `pydantic-settings` names match the environment variables injected via your Terraform/ArgoCD manifests.
- **Structured Logging**: Use `structlog` or standard JSON logging to ensure logs are easily searchable in cloud logging consoles (like Azure Monitor/Log Analytics).
