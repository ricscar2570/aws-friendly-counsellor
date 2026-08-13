from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from ...domain.entities import (
    AnalysisVersion,
    AuditContext,
    AuditEvent,
    Membership,
    Project,
    Tenant,
)
from ...domain.exceptions import ConflictError, NotFoundError, RevisionConflictError
from .common import decode_cursor, encode_cursor, new_id, utc_now


class DynamoDBStore:
    backend_name = "dynamodb"

    def __init__(self, table_name: str, region_name: str | None = None) -> None:
        import boto3

        self._resource = boto3.resource("dynamodb", region_name=region_name)
        self._table = self._resource.Table(table_name)
        self._client = self._table.meta.client
        self.table_name = table_name

    def initialize(self) -> None:
        return None

    def health_check(self) -> bool:
        self._client.describe_table(TableName=self.table_name)
        return True

    def close(self) -> None:
        return None

    @staticmethod
    def _to_native(value: Any) -> Any:
        if isinstance(value, Decimal):
            return int(value) if value % 1 == 0 else float(value)
        if isinstance(value, list):
            return [DynamoDBStore._to_native(item) for item in value]
        if isinstance(value, dict):
            return {key: DynamoDBStore._to_native(item) for key, item in value.items()}
        return value

    @staticmethod
    def _tenant(item: dict[str, Any]) -> Tenant:
        return Tenant(
            id=item["id"],
            name=item["name"],
            slug=item["slug"],
            status=item["status"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            revision=int(item["revision"]),
        )

    @staticmethod
    def _membership(item: dict[str, Any]) -> Membership:
        return Membership(
            tenant_id=item["tenant_id"],
            subject=item["subject"],
            role=item["role"],
            status=item["status"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            revision=int(item["revision"]),
        )

    @staticmethod
    def _project(item: dict[str, Any]) -> Project:
        return Project(
            id=item["id"],
            tenant_id=item["tenant_id"],
            name=item["name"],
            description=item["description"],
            estimated_users=int(item["estimated_users"]),
            budget=item["budget"],
            region=item["region"],
            status=item["status"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            revision=int(item["revision"]),
        )

    @staticmethod
    def _analysis(item: dict[str, Any]) -> AnalysisVersion:
        return AnalysisVersion(
            analysis_id=item["analysis_id"],
            tenant_id=item["tenant_id"],
            project_id=item["project_id"],
            version=int(item["version"]),
            request_payload=json.loads(item["request_json"]),
            result_payload=json.loads(item["result_json"]),
            created_at=item["created_at"],
        )

    @staticmethod
    def _audit(item: dict[str, Any]) -> AuditEvent:
        return AuditEvent(
            id=item["id"],
            tenant_id=item["tenant_id"],
            actor_subject=item["actor_subject"],
            action=item["action"],
            resource_type=item["resource_type"],
            resource_id=item["resource_id"],
            request_id=item["request_id"],
            occurred_at=item["occurred_at"],
            metadata=json.loads(item["metadata_json"]),
        )

    @staticmethod
    def _serialize_item(item: dict[str, Any]) -> dict[str, Any]:
        from boto3.dynamodb.types import TypeSerializer

        serializer = TypeSerializer()
        return {key: serializer.serialize(value) for key, value in item.items()}

    @staticmethod
    def _audit_item(
        *,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        audit: AuditContext | None,
    ) -> dict[str, Any] | None:
        if audit is None:
            return None
        event_id = new_id("aud")
        occurred_at = utc_now()
        return {
            "pk": f"TENANT#{tenant_id}",
            "sk": f"AUDIT#{occurred_at}#{event_id}",
            "entity_type": "audit_event",
            "id": event_id,
            "tenant_id": tenant_id,
            "actor_subject": audit.actor_subject,
            "action": audit.action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "request_id": audit.request_id,
            "occurred_at": occurred_at,
            "metadata_json": json.dumps(
                audit.metadata or {}, separators=(",", ":"), sort_keys=True
            ),
        }

    def _audit_put(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "Put": {
                "TableName": self.table_name,
                "Item": self._serialize_item(item),
                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
            }
        }

    def create_tenant(
        self,
        *,
        name: str,
        slug: str,
        owner_subject: str | None = None,
        audit: AuditContext | None = None,
    ) -> Tenant:
        now = utc_now()
        tenant = Tenant(
            id=new_id("ten"),
            name=name,
            slug=slug,
            status="active",
            created_at=now,
            updated_at=now,
            revision=1,
        )
        tenant_item = {
            "pk": f"TENANT#{tenant.id}",
            "sk": "METADATA",
            "entity_type": "tenant",
            **tenant.to_dict(),
        }
        slug_item = {
            "pk": f"TENANT_SLUG#{slug}",
            "sk": "LOCK",
            "entity_type": "tenant_slug_lock",
            "tenant_id": tenant.id,
        }
        items: list[dict[str, Any]] = [
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": self._serialize_item(tenant_item),
                    "ConditionExpression": "attribute_not_exists(pk)",
                }
            },
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": self._serialize_item(slug_item),
                    "ConditionExpression": "attribute_not_exists(pk)",
                }
            },
        ]
        if owner_subject is not None:
            membership_item = {
                "pk": f"TENANT#{tenant.id}",
                "sk": f"MEMBER#{owner_subject}",
                "entity_type": "membership",
                "tenant_id": tenant.id,
                "subject": owner_subject,
                "role": "owner",
                "status": "active",
                "created_at": now,
                "updated_at": now,
                "revision": 1,
            }
            items.append(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": self._serialize_item(membership_item),
                        "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                    }
                }
            )
        audit_item = self._audit_item(
            tenant_id=tenant.id,
            resource_type="tenant",
            resource_id=tenant.id,
            audit=audit,
        )
        if audit_item is not None:
            items.append(self._audit_put(audit_item))
        try:
            self._client.transact_write_items(TransactItems=items)
        except self._client.exceptions.TransactionCanceledException as exc:
            raise ConflictError("Tenant slug already exists") from exc
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        response = self._table.get_item(
            Key={"pk": f"TENANT#{tenant_id}", "sk": "METADATA"},
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            raise NotFoundError("Tenant not found")
        return self._tenant(self._to_native(item))

    def create_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        role: str,
        status: str = "active",
        audit: AuditContext | None = None,
    ) -> Membership:
        self.get_tenant(tenant_id)
        now = utc_now()
        membership = Membership(
            tenant_id=tenant_id,
            subject=subject,
            role=role,
            status=status,
            created_at=now,
            updated_at=now,
            revision=1,
        )
        item = {
            "pk": f"TENANT#{tenant_id}",
            "sk": f"MEMBER#{subject}",
            "entity_type": "membership",
            **membership.to_dict(),
        }
        audit_item = self._audit_item(
            tenant_id=tenant_id,
            resource_type="membership",
            resource_id=subject,
            audit=audit,
        )
        try:
            if audit_item is None:
                self._table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
                )
            else:
                self._client.transact_write_items(
                    TransactItems=[
                        {
                            "Put": {
                                "TableName": self.table_name,
                                "Item": self._serialize_item(item),
                                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                            }
                        },
                        self._audit_put(audit_item),
                    ]
                )
        except (
            self._client.exceptions.ConditionalCheckFailedException,
            self._client.exceptions.TransactionCanceledException,
        ) as exc:
            raise ConflictError("Tenant membership already exists") from exc
        return membership

    def get_membership(self, *, tenant_id: str, subject: str) -> Membership:
        response = self._table.get_item(
            Key={"pk": f"TENANT#{tenant_id}", "sk": f"MEMBER#{subject}"},
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            raise NotFoundError("Tenant membership not found")
        return self._membership(self._to_native(item))

    def list_memberships(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Membership], str | None]:
        from boto3.dynamodb.conditions import Key

        self.get_tenant(tenant_id)
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"TENANT#{tenant_id}")
            & Key("sk").begins_with("MEMBER#"),
            "Limit": limit,
            "ConsistentRead": True,
            "ScanIndexForward": True,
        }
        if cursor:
            decoded = decode_cursor(cursor)
            key = decoded.get("last_evaluated_key")
            if not isinstance(key, dict):
                raise ValueError("Invalid pagination cursor")
            kwargs["ExclusiveStartKey"] = key
        response = self._table.query(**kwargs)
        memberships = [
            self._membership(self._to_native(item)) for item in response.get("Items", [])
        ]
        last_key = response.get("LastEvaluatedKey")
        next_cursor = (
            encode_cursor({"last_evaluated_key": self._to_native(last_key)})
            if last_key
            else None
        )
        return memberships, next_cursor

    def update_membership(
        self,
        *,
        tenant_id: str,
        subject: str,
        expected_revision: int,
        role: str | None,
        status: str | None,
        audit: AuditContext | None = None,
    ) -> Membership:
        if role is None and status is None:
            return self.get_membership(tenant_id=tenant_id, subject=subject)
        names: dict[str, str] = {"#revision": "revision", "#updated_at": "updated_at"}
        values: dict[str, Any] = {
            ":expected_revision": expected_revision,
            ":next_revision": expected_revision + 1,
            ":updated_at": utc_now(),
        }
        assignments = ["#revision = :next_revision", "#updated_at = :updated_at"]
        if role is not None:
            names["#role"] = "role"
            values[":role"] = role
            assignments.append("#role = :role")
        if status is not None:
            names["#status"] = "status"
            values[":status"] = status
            assignments.append("#status = :status")
        key = {"pk": f"TENANT#{tenant_id}", "sk": f"MEMBER#{subject}"}
        audit_item = self._audit_item(
            tenant_id=tenant_id,
            resource_type="membership",
            resource_id=subject,
            audit=audit,
        )
        try:
            if audit_item is None:
                response = self._table.update_item(
                    Key=key,
                    UpdateExpression="SET " + ", ".join(assignments),
                    ConditionExpression="attribute_exists(pk) AND #revision = :expected_revision",
                    ExpressionAttributeNames=names,
                    ExpressionAttributeValues=values,
                    ReturnValues="ALL_NEW",
                )
                return self._membership(self._to_native(response["Attributes"]))
            update = {
                "TableName": self.table_name,
                "Key": self._serialize_item(key),
                "UpdateExpression": "SET " + ", ".join(assignments),
                "ConditionExpression": "attribute_exists(pk) AND #revision = :expected_revision",
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": self._serialize_item(values),
            }
            self._client.transact_write_items(
                TransactItems=[{"Update": update}, self._audit_put(audit_item)]
            )
            return self.get_membership(tenant_id=tenant_id, subject=subject)
        except (
            self._client.exceptions.ConditionalCheckFailedException,
            self._client.exceptions.TransactionCanceledException,
        ) as exc:
            try:
                current = self.get_membership(tenant_id=tenant_id, subject=subject)
            except NotFoundError:
                raise NotFoundError("Tenant membership not found") from exc
            raise RevisionConflictError(
                f"Membership revision changed; current revision is {current.revision}"
            ) from exc

    def create_project(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str,
        estimated_users: int,
        budget: str,
        region: str,
        status: str,
        audit: AuditContext | None = None,
    ) -> Project:
        self.get_tenant(tenant_id)
        now = utc_now()
        project = Project(
            id=new_id("prj"),
            tenant_id=tenant_id,
            name=name,
            description=description,
            estimated_users=estimated_users,
            budget=budget,
            region=region,
            status=status,
            created_at=now,
            updated_at=now,
            revision=1,
        )
        item = {
            "pk": f"TENANT#{tenant_id}",
            "sk": f"PROJECT#{project.id}",
            "entity_type": "project",
            "analysis_version_counter": 0,
            **project.to_dict(),
        }
        audit_item = self._audit_item(
            tenant_id=tenant_id,
            resource_type="project",
            resource_id=project.id,
            audit=audit,
        )
        try:
            if audit_item is None:
                self._table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
                )
            else:
                self._client.transact_write_items(
                    TransactItems=[
                        {
                            "Put": {
                                "TableName": self.table_name,
                                "Item": self._serialize_item(item),
                                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                            }
                        },
                        self._audit_put(audit_item),
                    ]
                )
        except (
            self._client.exceptions.ConditionalCheckFailedException,
            self._client.exceptions.TransactionCanceledException,
        ) as exc:
            raise ConflictError("Project already exists") from exc
        return project

    def list_projects(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[Project], str | None]:
        from boto3.dynamodb.conditions import Key

        self.get_tenant(tenant_id)
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"TENANT#{tenant_id}")
            & Key("sk").begins_with("PROJECT#"),
            "Limit": limit,
            "ConsistentRead": True,
        }
        if cursor:
            decoded = decode_cursor(cursor)
            key = decoded.get("last_evaluated_key")
            if not isinstance(key, dict):
                raise ValueError("Invalid pagination cursor")
            kwargs["ExclusiveStartKey"] = key
        response = self._table.query(**kwargs)
        projects = [self._project(self._to_native(item)) for item in response.get("Items", [])]
        last_key = response.get("LastEvaluatedKey")
        next_cursor = (
            encode_cursor({"last_evaluated_key": self._to_native(last_key)})
            if last_key
            else None
        )
        return projects, next_cursor

    def get_project(self, *, tenant_id: str, project_id: str) -> Project:
        response = self._table.get_item(
            Key={"pk": f"TENANT#{tenant_id}", "sk": f"PROJECT#{project_id}"},
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            raise NotFoundError("Project not found")
        return self._project(self._to_native(item))

    def update_project(
        self,
        *,
        tenant_id: str,
        project_id: str,
        expected_revision: int,
        changes: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> Project:
        if not changes:
            return self.get_project(tenant_id=tenant_id, project_id=project_id)
        allowed = {"name", "description", "estimated_users", "budget", "region", "status"}
        invalid = set(changes) - allowed
        if invalid:
            raise ValueError(f"Unsupported project fields: {sorted(invalid)}")
        names: dict[str, str] = {"#revision": "revision", "#updated_at": "updated_at"}
        values: dict[str, Any] = {
            ":expected_revision": expected_revision,
            ":next_revision": expected_revision + 1,
            ":updated_at": utc_now(),
        }
        assignments = ["#revision = :next_revision", "#updated_at = :updated_at"]
        for index, (field, value) in enumerate(changes.items()):
            name_token = f"#f{index}"
            value_token = f":v{index}"
            names[name_token] = field
            values[value_token] = value
            assignments.append(f"{name_token} = {value_token}")
        key = {"pk": f"TENANT#{tenant_id}", "sk": f"PROJECT#{project_id}"}
        audit_item = self._audit_item(
            tenant_id=tenant_id,
            resource_type="project",
            resource_id=project_id,
            audit=audit,
        )
        try:
            if audit_item is None:
                response = self._table.update_item(
                    Key=key,
                    UpdateExpression="SET " + ", ".join(assignments),
                    ConditionExpression="attribute_exists(pk) AND #revision = :expected_revision",
                    ExpressionAttributeNames=names,
                    ExpressionAttributeValues=values,
                    ReturnValues="ALL_NEW",
                )
                return self._project(self._to_native(response["Attributes"]))
            update = {
                "TableName": self.table_name,
                "Key": self._serialize_item(key),
                "UpdateExpression": "SET " + ", ".join(assignments),
                "ConditionExpression": "attribute_exists(pk) AND #revision = :expected_revision",
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": self._serialize_item(values),
            }
            self._client.transact_write_items(
                TransactItems=[{"Update": update}, self._audit_put(audit_item)]
            )
            return self.get_project(tenant_id=tenant_id, project_id=project_id)
        except (
            self._client.exceptions.ConditionalCheckFailedException,
            self._client.exceptions.TransactionCanceledException,
        ) as exc:
            try:
                current = self.get_project(tenant_id=tenant_id, project_id=project_id)
            except NotFoundError:
                raise NotFoundError("Project not found") from exc
            raise RevisionConflictError(
                f"Project revision changed; current revision is {current.revision}"
            ) from exc

    def create_analysis_version(
        self,
        *,
        tenant_id: str,
        project_id: str,
        request_payload: dict[str, Any],
        result_payload: dict[str, Any],
        audit: AuditContext | None = None,
    ) -> AnalysisVersion:
        project_key = {"pk": f"TENANT#{tenant_id}", "sk": f"PROJECT#{project_id}"}
        for _ in range(5):
            response = self._table.get_item(Key=project_key, ConsistentRead=True)
            project_item = response.get("Item")
            if not project_item:
                raise NotFoundError("Project not found")
            current = int(project_item.get("analysis_version_counter", 0))
            version = current + 1
            now = utc_now()
            analysis = AnalysisVersion(
                analysis_id=new_id("ana"),
                tenant_id=tenant_id,
                project_id=project_id,
                version=version,
                request_payload=request_payload,
                result_payload=result_payload,
                created_at=now,
            )
            analysis_item = {
                "pk": f"TENANT#{tenant_id}#PROJECT#{project_id}",
                "sk": f"ANALYSIS#{version:012d}",
                "entity_type": "analysis_version",
                "analysis_id": analysis.analysis_id,
                "tenant_id": tenant_id,
                "project_id": project_id,
                "version": version,
                "request_json": json.dumps(request_payload, separators=(",", ":"), sort_keys=True),
                "result_json": json.dumps(result_payload, separators=(",", ":"), sort_keys=True),
                "created_at": now,
            }
            condition = (
                "attribute_not_exists(analysis_version_counter)"
                if current == 0
                else "analysis_version_counter = :current"
            )
            update: dict[str, Any] = {
                "TableName": self.table_name,
                "Key": self._serialize_item(project_key),
                "UpdateExpression": "SET analysis_version_counter = :next",
                "ConditionExpression": f"attribute_exists(pk) AND {condition}",
                "ExpressionAttributeValues": self._serialize_item(
                    {":next": version, **({":current": current} if current else {})}
                ),
            }
            items: list[dict[str, Any]] = [
                {"Update": update},
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": self._serialize_item(analysis_item),
                        "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                    }
                },
            ]
            audit_item = self._audit_item(
                tenant_id=tenant_id,
                resource_type="analysis",
                resource_id=analysis.analysis_id,
                audit=audit,
            )
            if audit_item is not None:
                items.append(self._audit_put(audit_item))
            try:
                self._client.transact_write_items(TransactItems=items)
                return analysis
            except self._client.exceptions.TransactionCanceledException:
                continue
        raise ConflictError("Could not allocate an analysis version after concurrent updates")

    def list_analysis_versions(
        self, *, tenant_id: str, project_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AnalysisVersion], str | None]:
        from boto3.dynamodb.conditions import Key

        self.get_project(tenant_id=tenant_id, project_id=project_id)
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"TENANT#{tenant_id}#PROJECT#{project_id}")
            & Key("sk").begins_with("ANALYSIS#"),
            "Limit": limit,
            "ConsistentRead": True,
            "ScanIndexForward": True,
        }
        if cursor:
            decoded = decode_cursor(cursor)
            key = decoded.get("last_evaluated_key")
            if not isinstance(key, dict):
                raise ValueError("Invalid pagination cursor")
            kwargs["ExclusiveStartKey"] = key
        response = self._table.query(**kwargs)
        analyses = [self._analysis(self._to_native(item)) for item in response.get("Items", [])]
        last_key = response.get("LastEvaluatedKey")
        next_cursor = (
            encode_cursor({"last_evaluated_key": self._to_native(last_key)})
            if last_key
            else None
        )
        return analyses, next_cursor

    def get_analysis_version(
        self, *, tenant_id: str, project_id: str, version: int
    ) -> AnalysisVersion:
        response = self._table.get_item(
            Key={
                "pk": f"TENANT#{tenant_id}#PROJECT#{project_id}",
                "sk": f"ANALYSIS#{version:012d}",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            raise NotFoundError("Analysis version not found")
        return self._analysis(self._to_native(item))

    def list_audit_events(
        self, *, tenant_id: str, limit: int, cursor: str | None
    ) -> tuple[list[AuditEvent], str | None]:
        from boto3.dynamodb.conditions import Key

        self.get_tenant(tenant_id)
        kwargs: dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"TENANT#{tenant_id}")
            & Key("sk").begins_with("AUDIT#"),
            "Limit": limit,
            "ConsistentRead": True,
            "ScanIndexForward": False,
        }
        if cursor:
            decoded = decode_cursor(cursor)
            key = decoded.get("last_evaluated_key")
            if not isinstance(key, dict):
                raise ValueError("Invalid pagination cursor")
            kwargs["ExclusiveStartKey"] = key
        response = self._table.query(**kwargs)
        events = [self._audit(self._to_native(item)) for item in response.get("Items", [])]
        last_key = response.get("LastEvaluatedKey")
        next_cursor = (
            encode_cursor({"last_evaluated_key": self._to_native(last_key)})
            if last_key
            else None
        )
        return events, next_cursor
