# Service Auth Contract v1

This document defines the long-term, shared auth contract for MiniPaaS microservices.

## Goal

All backend services must validate end-user identity through auth-service, not by duplicating JWT decode logic in each service.

## Standard Flow

1. Client sends `Authorization: Bearer <access_token>` to a service.
2. Service forwards token to auth-service:
   - `GET /auth/me`
   - Header: `Authorization: Bearer <access_token>`
3. Auth-service returns user identity payload.
4. Service uses returned `id` as authoritative `user_id`.

## Auth-Service Contract

### Request

`GET /auth/me`

Headers:

```http
Authorization: Bearer <access_token>
```

### Success Response (200)

```json
{
  "id": 2,
  "email": "user@example.com",
  "name": "User Name",
  "oauth_provider": "github",
  "has_password": false
}
```

Required field for service contracts: `id`.

### Error Responses

- `401` invalid/expired token
- `403` user disabled/deactivated

## Service Error Mapping Recommendation

- auth-service unreachable: return `503`
- auth-service malformed response: return `502`
- auth-service 401/403: return `401` (or `403` if you preserve deactivated semantics)

## Endpoint Design Guidance

- Prefer user-scoped routes over path user IDs:
  - Use `/resource/me` instead of `/resource/user/{user_id}`
- If legacy `/user/{user_id}` exists, enforce `token_user_id == path_user_id`.

## Deprecations

- Legacy introspection endpoint `POST /verify` is deprecated for new services.
- New services must implement v1 flow via `GET /auth/me`.
