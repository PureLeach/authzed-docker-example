from enum import StrEnum
from typing import Optional, Union

from pydantic import field_validator
from pydantic.dataclasses import dataclass


class RelationUpdateType(StrEnum):
    create = "create"
    grant = "grant"
    revoke = "revoke"


class Access(StrEnum):
    allow = "allow"
    forbid = "forbid"
    undefined = "undefined"

    def is_allowed(self) -> bool:
        return self == self.allow


@dataclass(frozen=True, slots=True)
class CheckRequest:
    subject_type: str
    subject_id: Union[str, int]
    resource_type: str
    resource_id: Union[str, int]
    permission: str

    @field_validator("subject_id", mode="before")
    @staticmethod
    def subject_id_validator(raw_subject_id: str | int) -> str:
        return str(raw_subject_id)

    @field_validator("resource_id", mode="before")
    @staticmethod
    def object_id_validator(raw_resource_id: str | int) -> str:
        return str(raw_resource_id)


@dataclass(frozen=True, slots=True)
class ResourcesRequest:
    subject_type: str
    subject_id: Union[str, int]
    resource_type: str
    permission: str


@dataclass(frozen=True, slots=True)
class RelationUpdateRequest:
    subject_type: str
    subject_id: Union[str, int]
    resource_type: str
    resource_id: Union[str, int]
    relation: str
    subject_relation: str = ""
    update_type: Optional[RelationUpdateType] = None


@dataclass(frozen=True, slots=True)
class RelationUpdateGrantRequest(RelationUpdateRequest):
    update_type: RelationUpdateType = RelationUpdateType.grant


@dataclass(frozen=True, slots=True)
class RelationUpdateRevokeRequest(RelationUpdateRequest):
    update_type: RelationUpdateType = RelationUpdateType.revoke


@dataclass(frozen=True, slots=True)
class ResourcesWithRelations:
    resource_id: str
    relations: list[str]


@dataclass(frozen=True, slots=True)
class SubjectsWithRelations:
    subject_type: str | None
    subject_id: str
    relations: list[str]
