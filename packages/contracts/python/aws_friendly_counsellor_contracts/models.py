from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONTRACT_VERSION = "1.3.0"

SUPPORTED_REGIONS = {
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-central-1",
    "eu-central-2",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
}

BudgetProfile = Literal["low", "medium", "high"]
ProjectStatus = Literal["draft", "active", "archived"]
TenantStatus = Literal["active", "suspended"]
TenantRole = Literal["viewer", "editor", "admin", "owner"]
MembershipStatus = Literal["active", "suspended"]


class ContractModel(BaseModel):
    """Shared strict base for public API contracts."""

    model_config = ConfigDict(extra="forbid")


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _validate_region(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_REGIONS:
        raise ValueError(
            "Unsupported region. Use a supported AWS commercial region such as "
            "us-east-1, eu-west-1, eu-central-1, or eu-north-1."
        )
    return normalized


class AnalysisRequest(ContractModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Plain-language project description.",
        examples=[
            "A web application with customer login, file uploads, and analytics dashboard"
        ],
    )
    estimated_users: int = Field(
        ...,
        ge=1,
        le=100_000_000,
        description="Estimated monthly active users.",
        examples=[5000],
    )
    budget: BudgetProfile = Field(
        ...,
        description="Relative budget constraint used by the deterministic planner.",
        examples=["medium"],
    )
    region: str = Field(
        default="us-east-1",
        description="Target AWS commercial region.",
        examples=["eu-central-1"],
    )
    advanced_guide: bool = Field(
        default=True,
        description="Whether to include extended operational guidance.",
    )

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = _normalize_text(value)
        if len(normalized) < 10:
            raise ValueError("Description too short")
        return normalized

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        return _validate_region(value)


class RootResponse(ContractModel):
    service: str
    version: str
    release_version: str
    environment: Literal["local", "test", "dev", "staging", "production"]
    status: Literal["healthy"]
    docs: str
    api_version: Literal["v1"]


class HealthResponse(ContractModel):
    status: Literal["healthy"]
    check: Literal["combined", "liveness", "readiness"]
    timestamp: str
    version: str
    release_version: str
    git_sha: str
    environment: Literal["local", "test", "dev", "staging", "production"]
    api_version: Literal["v1"]
    persistence_backend: Literal["sqlite", "dynamodb"] | None = None
    persistence_status: Literal["available"] | None = None


class ResponseMetadata(ContractModel):
    request_id: str
    processing_time_ms: int = Field(ge=0)
    timestamp: str
    version: str
    contract_version: str


class AnalysisSummary(ContractModel):
    project_type: str
    confidence: float = Field(ge=0, le=1)
    detected_features: list[str]
    classifier: str


class ServiceRecommendation(ContractModel):
    id: str
    name: str
    category: str
    essential: bool
    typical_monthly: str
    free_tier: str
    why_needed: str
    use_case_example: str
    region: str


class CostSummary(ContractModel):
    free_tier_viable: bool
    minimum: str
    typical: str
    maximum: str
    minimum_value: float = Field(ge=0)
    typical_value: float = Field(ge=0)
    maximum_value: float = Field(ge=0)
    budget_alignment: str


class CostBreakdownItem(ContractModel):
    name: str
    minimum: float = Field(ge=0)
    maximum: float = Field(ge=0)
    display: str
    free_tier: str


class CostAnalysis(ContractModel):
    currency: Literal["USD"]
    period: Literal["monthly"]
    region: str
    summary: CostSummary
    breakdown: dict[str, CostBreakdownItem]
    assumptions: list[str]


class GuideProjectContext(ContractModel):
    type: str
    estimated_monthly_active_users: int = Field(ge=1)
    budget: BudgetProfile
    region: str
    services_count: int = Field(ge=0)
    complexity: str


class GuideIntroduction(ContractModel):
    title: str
    overview: str
    estimated_effort: str
    estimated_monthly_cost: str


class GuidePhase(ContractModel):
    name: str
    duration: str
    steps: list[str]


class GuideOperations(ContractModel):
    security: list[str]
    reliability: list[str]
    cost_control: list[str]


class ImplementationGuide(ContractModel):
    format: Literal["essential", "advanced"]
    project_context: GuideProjectContext
    introduction: GuideIntroduction
    prerequisites: list[str]
    phases: list[GuidePhase]
    acceptance_checks: list[str]
    operations: GuideOperations | None = None


class AnalyzeResponse(ContractModel):
    project_id: str
    analysis: AnalysisSummary
    services: list[ServiceRecommendation]
    cost_analysis: CostAnalysis
    implementation_guide: ImplementationGuide
    metadata: ResponseMetadata


class IaCAnalysisSummary(ContractModel):
    project_type: str
    services_count: int = Field(ge=0)
    region: str


class TerraformBundle(ContractModel):
    format: Literal["terraform"]
    status: Literal["baseline_ready"]
    supported_services: list[str]
    deferred_services: list[str]
    files: dict[str, str]
    instructions: list[str]


class IaCResponse(ContractModel):
    project_id: str
    analysis: IaCAnalysisSummary
    terraform: TerraformBundle
    metadata: ResponseMetadata


class NarrativeResponse(ContractModel):
    project_id: str
    narrative_html: str
    metadata: ResponseMetadata


class TenantCreateRequest(ContractModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=63)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            raise ValueError("Slug must contain lowercase letters, digits, and hyphens")
        return normalized


class TenantRecord(ContractModel):
    id: str
    name: str
    slug: str
    status: TenantStatus
    created_at: str
    updated_at: str
    revision: int = Field(ge=1)


class TenantResponse(ContractModel):
    tenant: TenantRecord
    metadata: ResponseMetadata


class ProjectCreateRequest(ContractModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=5000)
    estimated_users: int = Field(ge=1, le=100_000_000)
    budget: BudgetProfile
    region: str = "us-east-1"
    status: ProjectStatus = "draft"

    @field_validator("name", "description")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        return _validate_region(value)


class ProjectUpdateRequest(ContractModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    estimated_users: int | None = Field(default=None, ge=1, le=100_000_000)
    budget: BudgetProfile | None = None
    region: str | None = None
    status: ProjectStatus | None = None

    @field_validator("name", "description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_text(value) if value is not None else None

    @field_validator("region")
    @classmethod
    def validate_optional_region(cls, value: str | None) -> str | None:
        return _validate_region(value) if value is not None else None

    @model_validator(mode="after")
    def require_change(self) -> "ProjectUpdateRequest":
        if not any(
            getattr(self, field) is not None
            for field in (
                "name",
                "description",
                "estimated_users",
                "budget",
                "region",
                "status",
            )
        ):
            raise ValueError("At least one project field must be changed")
        return self


class ProjectRecord(ContractModel):
    id: str
    tenant_id: str
    name: str
    description: str
    estimated_users: int = Field(ge=1)
    budget: BudgetProfile
    region: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    revision: int = Field(ge=1)


class ProjectResponse(ContractModel):
    project: ProjectRecord
    metadata: ResponseMetadata


class ProjectListResponse(ContractModel):
    projects: list[ProjectRecord]
    next_cursor: str | None = None
    metadata: ResponseMetadata


class ProjectAnalysisCreateRequest(ContractModel):
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    estimated_users: int | None = Field(default=None, ge=1, le=100_000_000)
    budget: BudgetProfile | None = None
    region: str | None = None
    advanced_guide: bool = True

    @field_validator("description")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        return _normalize_text(value) if value is not None else None

    @field_validator("region")
    @classmethod
    def validate_optional_region(cls, value: str | None) -> str | None:
        return _validate_region(value) if value is not None else None


class AnalysisVersionRecord(ContractModel):
    analysis_id: str
    tenant_id: str
    project_id: str
    version: int = Field(ge=1)
    request: AnalysisRequest
    result: AnalyzeResponse
    created_at: str


class AnalysisVersionResponse(ContractModel):
    analysis_version: AnalysisVersionRecord
    metadata: ResponseMetadata


class AnalysisVersionSummary(ContractModel):
    analysis_id: str
    project_id: str
    version: int = Field(ge=1)
    project_type: str
    typical_monthly_cost: str
    created_at: str


class AnalysisVersionListResponse(ContractModel):
    analysis_versions: list[AnalysisVersionSummary]
    next_cursor: str | None = None
    metadata: ResponseMetadata


class IdentityResponse(ContractModel):
    subject: str
    username: str | None = None
    metadata: ResponseMetadata


class TenantMembershipCreateRequest(ContractModel):
    subject: str = Field(min_length=1, max_length=256)
    role: TenantRole = "viewer"

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9._:@+\-/=]{1,256}", normalized):
            raise ValueError("Subject contains unsupported characters")
        return normalized


class TenantMembershipUpdateRequest(ContractModel):
    expected_revision: int = Field(ge=1)
    role: TenantRole | None = None
    status: MembershipStatus | None = None

    @model_validator(mode="after")
    def require_membership_change(self) -> "TenantMembershipUpdateRequest":
        if self.role is None and self.status is None:
            raise ValueError("At least one membership field must be changed")
        return self


class TenantMembershipRecord(ContractModel):
    tenant_id: str
    subject: str
    role: TenantRole
    status: MembershipStatus
    created_at: str
    updated_at: str
    revision: int = Field(ge=1)


class TenantMembershipResponse(ContractModel):
    membership: TenantMembershipRecord
    metadata: ResponseMetadata


class TenantMembershipListResponse(ContractModel):
    memberships: list[TenantMembershipRecord]
    next_cursor: str | None = None
    metadata: ResponseMetadata


class AuditEventRecord(ContractModel):
    id: str
    tenant_id: str
    actor_subject: str
    action: str
    resource_type: str
    resource_id: str
    request_id: str
    occurred_at: str
    metadata: dict[str, Any]


class AuditEventListResponse(ContractModel):
    audit_events: list[AuditEventRecord]
    next_cursor: str | None = None
    metadata: ResponseMetadata


class ErrorItem(ContractModel):
    code: str
    message: str
    request_id: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(ContractModel):
    error: ErrorItem


TOP_LEVEL_CONTRACT_MODELS: tuple[type[BaseModel], ...] = (
    AnalysisRequest,
    AnalyzeResponse,
    IaCResponse,
    NarrativeResponse,
    RootResponse,
    HealthResponse,
    TenantCreateRequest,
    TenantResponse,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectAnalysisCreateRequest,
    AnalysisVersionResponse,
    AnalysisVersionListResponse,
    IdentityResponse,
    TenantMembershipCreateRequest,
    TenantMembershipUpdateRequest,
    TenantMembershipResponse,
    TenantMembershipListResponse,
    AuditEventListResponse,
    ErrorResponse,
)
