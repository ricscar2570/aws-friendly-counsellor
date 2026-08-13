from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from aws_friendly_counsellor.domain.entities import Project
from aws_friendly_counsellor.domain.exceptions import (
    ConflictError,
    NotFoundError,
    RevisionConflictError,
)
from aws_friendly_counsellor.infrastructure.persistence.common import decode_cursor
from aws_friendly_counsellor.infrastructure.persistence.dynamodb_store import DynamoDBStore


class ConditionalCheckFailedException(Exception):
    pass


class TransactionCanceledException(Exception):
    pass


def make_store() -> DynamoDBStore:
    store = object.__new__(DynamoDBStore)
    store.table_name = "awsfc-test"
    store._table = MagicMock()
    store._client = MagicMock()
    store._client.exceptions = SimpleNamespace(
        ConditionalCheckFailedException=ConditionalCheckFailedException,
        TransactionCanceledException=TransactionCanceledException,
    )
    return store


def tenant_item() -> dict:
    return {
        "id": "ten_aaaaaaaaaaaaaaaaaaaaaaaa",
        "name": "Acme",
        "slug": "acme",
        "status": "active",
        "created_at": "2026-08-01T00:00:00+00:00",
        "updated_at": "2026-08-01T00:00:00+00:00",
        "revision": Decimal("1"),
    }


def project_item() -> dict:
    return {
        "id": "prj_bbbbbbbbbbbbbbbbbbbbbbbb",
        "tenant_id": "ten_aaaaaaaaaaaaaaaaaaaaaaaa",
        "name": "Portal",
        "description": "A sufficiently detailed customer portal",
        "estimated_users": Decimal("1000"),
        "budget": "medium",
        "region": "eu-central-1",
        "status": "active",
        "created_at": "2026-08-01T00:00:00+00:00",
        "updated_at": "2026-08-01T00:00:00+00:00",
        "revision": Decimal("1"),
    }


def analysis_item() -> dict:
    return {
        "analysis_id": "ana_cccccccccccccccccccccccc",
        "tenant_id": "ten_aaaaaaaaaaaaaaaaaaaaaaaa",
        "project_id": "prj_bbbbbbbbbbbbbbbbbbbbbbbb",
        "version": Decimal("1"),
        "request_json": '{"description":"A detailed portal","estimated_users":1000,"budget":"medium","region":"eu-central-1","advanced_guide":true}',
        "result_json": '{"analysis":{"project_type":"web_application"},"cost_analysis":{"summary":{"typical":"$10"}}}',
        "created_at": "2026-08-01T00:00:00+00:00",
    }


def test_constructor_health_and_native_conversion(monkeypatch):
    table = MagicMock()
    client = MagicMock()
    table.meta.client = client
    resource = MagicMock()
    resource.Table.return_value = table
    monkeypatch.setattr("boto3.resource", lambda *args, **kwargs: resource)

    store = DynamoDBStore("awsfc-test", region_name="eu-central-1")
    assert store.table_name == "awsfc-test"
    store.initialize()
    assert store.health_check() is True
    client.describe_table.assert_called_once_with(TableName="awsfc-test")
    store.close()
    assert store._to_native({"n": Decimal("2"), "f": Decimal("2.5"), "l": [Decimal("3")]}) == {
        "n": 2,
        "f": 2.5,
        "l": [3],
    }


def test_tenant_create_get_and_conflict():
    store = make_store()
    created = store.create_tenant(name="Acme", slug="acme")
    assert created.slug == "acme"
    assert store._client.transact_write_items.called

    store._table.get_item.return_value = {"Item": tenant_item()}
    assert store.get_tenant(tenant_item()["id"]).name == "Acme"
    store._table.get_item.return_value = {}
    with pytest.raises(NotFoundError):
        store.get_tenant(tenant_item()["id"])

    store._client.transact_write_items.side_effect = TransactionCanceledException()
    with pytest.raises(ConflictError):
        store.create_tenant(name="Other", slug="acme")


def test_project_create_get_list_and_conflict(monkeypatch):
    store = make_store()
    monkeypatch.setattr(store, "get_tenant", lambda tenant_id: None)
    project = store.create_project(
        tenant_id=tenant_item()["id"],
        name="Portal",
        description="A sufficiently detailed customer portal",
        estimated_users=1000,
        budget="medium",
        region="eu-central-1",
        status="active",
    )
    assert project.tenant_id == tenant_item()["id"]
    assert store._table.put_item.called

    store._table.get_item.return_value = {"Item": project_item()}
    assert store.get_project(
        tenant_id=tenant_item()["id"], project_id=project_item()["id"]
    ).name == "Portal"
    store._table.get_item.return_value = {}
    with pytest.raises(NotFoundError):
        store.get_project(tenant_id=tenant_item()["id"], project_id=project_item()["id"])

    store._table.query.return_value = {
        "Items": [project_item()],
        "LastEvaluatedKey": {"pk": "TENANT#x", "sk": "PROJECT#x"},
    }
    projects, cursor = store.list_projects(
        tenant_id=tenant_item()["id"], limit=1, cursor=None
    )
    assert projects[0].id == project_item()["id"]
    assert decode_cursor(cursor)["last_evaluated_key"]["sk"] == "PROJECT#x"
    store._table.query.return_value = {"Items": []}
    projects, cursor = store.list_projects(
        tenant_id=tenant_item()["id"], limit=1, cursor=cursor
    )
    assert projects == [] and cursor is None

    store._table.put_item.side_effect = ConditionalCheckFailedException()
    with pytest.raises(ConflictError):
        store.create_project(
            tenant_id=tenant_item()["id"],
            name="Portal",
            description="A sufficiently detailed customer portal",
            estimated_users=1000,
            budget="medium",
            region="eu-central-1",
            status="active",
        )


def test_project_update_success_stale_revision_and_missing(monkeypatch):
    store = make_store()
    updated_item = {**project_item(), "name": "Renamed", "revision": Decimal("2")}
    store._table.update_item.return_value = {"Attributes": updated_item}
    updated = store.update_project(
        tenant_id=tenant_item()["id"],
        project_id=project_item()["id"],
        expected_revision=1,
        changes={"name": "Renamed"},
    )
    assert updated.name == "Renamed" and updated.revision == 2

    existing = Project(**{**DynamoDBStore._project(project_item()).to_dict(), "revision": 3})
    store._table.update_item.side_effect = ConditionalCheckFailedException()
    monkeypatch.setattr(store, "get_project", lambda **kwargs: existing)
    with pytest.raises(RevisionConflictError):
        store.update_project(
            tenant_id=tenant_item()["id"],
            project_id=project_item()["id"],
            expected_revision=1,
            changes={"name": "Stale"},
        )

    monkeypatch.setattr(store, "get_project", MagicMock(side_effect=NotFoundError("missing")))
    with pytest.raises(NotFoundError):
        store.update_project(
            tenant_id=tenant_item()["id"],
            project_id=project_item()["id"],
            expected_revision=1,
            changes={"name": "Missing"},
        )


def test_analysis_create_list_get_and_retry_failure(monkeypatch):
    store = make_store()
    store._table.get_item.return_value = {"Item": {**project_item(), "analysis_version_counter": 0}}
    created = store.create_analysis_version(
        tenant_id=tenant_item()["id"],
        project_id=project_item()["id"],
        request_payload={"description": "request"},
        result_payload={"analysis": {"project_type": "web_application"}},
    )
    assert created.version == 1
    assert store._client.transact_write_items.called

    monkeypatch.setattr(store, "get_project", lambda **kwargs: DynamoDBStore._project(project_item()))
    store._table.query.return_value = {
        "Items": [analysis_item()],
        "LastEvaluatedKey": {"pk": "P", "sk": "ANALYSIS#1"},
    }
    items, cursor = store.list_analysis_versions(
        tenant_id=tenant_item()["id"], project_id=project_item()["id"], limit=1, cursor=None
    )
    assert items[0].version == 1 and cursor
    store._table.query.return_value = {"Items": []}
    items, next_cursor = store.list_analysis_versions(
        tenant_id=tenant_item()["id"], project_id=project_item()["id"], limit=1, cursor=cursor
    )
    assert items == [] and next_cursor is None

    store._table.get_item.return_value = {"Item": analysis_item()}
    assert store.get_analysis_version(
        tenant_id=tenant_item()["id"], project_id=project_item()["id"], version=1
    ).analysis_id == analysis_item()["analysis_id"]
    store._table.get_item.return_value = {}
    with pytest.raises(NotFoundError):
        store.get_analysis_version(
            tenant_id=tenant_item()["id"], project_id=project_item()["id"], version=1
        )

    store._table.get_item.return_value = {"Item": {**project_item(), "analysis_version_counter": 4}}
    store._client.transact_write_items.side_effect = TransactionCanceledException()
    with pytest.raises(ConflictError):
        store.create_analysis_version(
            tenant_id=tenant_item()["id"],
            project_id=project_item()["id"],
            request_payload={},
            result_payload={},
        )

    store._table.get_item.return_value = {}
    with pytest.raises(NotFoundError):
        store.create_analysis_version(
            tenant_id=tenant_item()["id"],
            project_id=project_item()["id"],
            request_payload={},
            result_payload={},
        )


def membership_item() -> dict:
    return {
        "tenant_id": tenant_item()["id"],
        "subject": "00000000-0000-4000-8000-000000000004",
        "role": "viewer",
        "status": "active",
        "created_at": "2026-08-01T00:00:00+00:00",
        "updated_at": "2026-08-01T00:00:00+00:00",
        "revision": Decimal("1"),
    }


def audit_item() -> dict:
    return {
        "id": "aud_dddddddddddddddddddddddd",
        "tenant_id": tenant_item()["id"],
        "actor_subject": "00000000-0000-4000-8000-000000000001",
        "action": "membership.created",
        "resource_type": "membership",
        "resource_id": membership_item()["subject"],
        "request_id": "req-test",
        "occurred_at": "2026-08-01T00:00:01+00:00",
        "metadata_json": '{"role":"viewer"}',
    }


def test_membership_create_read_update_and_list(monkeypatch):
    store = make_store()
    monkeypatch.setattr(store, "get_tenant", lambda tenant_id: None)
    created = store.create_membership(
        tenant_id=tenant_item()["id"],
        subject=membership_item()["subject"],
        role="viewer",
    )
    assert created.role == "viewer"
    assert store._table.put_item.called

    store._table.get_item.return_value = {"Item": membership_item()}
    assert store.get_membership(
        tenant_id=tenant_item()["id"], subject=membership_item()["subject"]
    ).subject == membership_item()["subject"]

    store._table.query.return_value = {
        "Items": [membership_item()],
        "LastEvaluatedKey": {"pk": "TENANT#x", "sk": "MEMBER#x"},
    }
    memberships, cursor = store.list_memberships(
        tenant_id=tenant_item()["id"], limit=1, cursor=None
    )
    assert memberships[0].role == "viewer" and cursor

    updated = {**membership_item(), "role": "editor", "revision": Decimal("2")}
    store._table.update_item.return_value = {"Attributes": updated}
    result = store.update_membership(
        tenant_id=tenant_item()["id"],
        subject=membership_item()["subject"],
        expected_revision=1,
        role="editor",
        status=None,
    )
    assert result.role == "editor" and result.revision == 2


def test_audit_listing_and_transactional_audit_write(monkeypatch):
    from aws_friendly_counsellor.domain.entities import AuditContext

    store = make_store()
    monkeypatch.setattr(store, "get_tenant", lambda tenant_id: None)
    audit = AuditContext(
        actor_subject="00000000-0000-4000-8000-000000000001",
        action="membership.created",
        request_id="req-test",
        metadata={"role": "viewer"},
    )
    store.create_membership(
        tenant_id=tenant_item()["id"],
        subject=membership_item()["subject"],
        role="viewer",
        audit=audit,
    )
    transaction = store._client.transact_write_items.call_args.kwargs["TransactItems"]
    assert len(transaction) == 2
    assert "Put" in transaction[0] and "Put" in transaction[1]

    store._table.query.return_value = {"Items": [audit_item()]}
    events, cursor = store.list_audit_events(
        tenant_id=tenant_item()["id"], limit=25, cursor=None
    )
    assert cursor is None
    assert events[0].action == "membership.created"
    assert events[0].metadata == {"role": "viewer"}
