# Identity and tenant authorization

## Why Cognito identity and tenant roles are separate

A Cognito user can participate in more than one customer tenant and can legitimately have different authority in each. Cognito therefore proves identity (`sub`), while application persistence owns tenant membership and role.

Cognito groups are not the tenant authorization source of truth in M1.4.

## Request contract

Protected deployed requests send:

```http
Authorization: Bearer <Cognito token>
X-Tenant-ID: ten_<24 hex characters>
```

`Authorization` proves identity at API Gateway. `X-Tenant-ID` merely selects which membership must be checked.

## Route authorization

- non-tenant planning routes require authenticated identity;
- tenant/project/analysis reads require at least `viewer`;
- project/analysis mutations require at least `editor`;
- membership and audit reads require at least `admin`;
- admins can manage only viewer/editor memberships;
- owners can manage all membership roles, except their own owner membership in this milestone.

## Local development

`X-Debug-Subject` is accepted only when all of the following are true:

- `APP_ENVIRONMENT` is `local` or `test`;
- `ALLOW_LOCAL_IDENTITY=true`;
- the subject passes the same bounded identifier validation.

The production CORS configuration does not expose debug identity headers, and the runtime refuses the shim in `dev`, `staging`, and `production` regardless of the flag.
