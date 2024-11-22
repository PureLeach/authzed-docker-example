import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Sequence, Union
from models import (
    Access,
    CheckRequest,
    RelationUpdateGrantRequest,
    RelationUpdateRequest,
    RelationUpdateRevokeRequest,
    RelationUpdateType,
    ResourcesRequest,
    ResourcesWithRelations,
    SubjectsWithRelations,
)


class BaseAuthzed(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("Authzed").getChild(self.__class__.__name__)

    @abstractmethod
    async def check(
        self,
        request: CheckRequest,
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> Access:
        raise NotImplementedError()

    async def is_allowed(
        self,
        request: CheckRequest,
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> bool:
        params = {}
        if minimize_latency:
            params["minimize_latency"] = minimize_latency
        else:
            params["full_consistent"] = full_consistent  # type: ignore[assignment]
        return (
            await self.check(
                request=request,
                **params,
            )
        ).is_allowed()

    @abstractmethod
    async def check_many(
        self,
        requests: list[CheckRequest],
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> dict[CheckRequest, Access]:
        raise NotImplementedError()

    async def is_allowed_many(
        self,
        requests: list[CheckRequest],
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> dict[CheckRequest, bool]:
        params = {}
        if minimize_latency:
            params["minimize_latency"] = minimize_latency
        else:
            params["full_consistent"] = full_consistent
        results_list = await self.check_many(
            requests=requests,
            **params,
        )
        return {
            request: response.is_allowed() for request, response in results_list.items()
        }

    async def grant(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        relation: str,
        subject_type: str,
        subject_id: Union[str, int],
        subject_relation: str = "",
    ) -> None:
        return await self.update(
            updates=[
                RelationUpdateRequest(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    relation=relation,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    update_type=RelationUpdateType.grant,
                    subject_relation=subject_relation,
                ),
            ]
        )

    async def grant_many(
        self,
        updates: Sequence[RelationUpdateGrantRequest],
    ) -> None:
        return await self.update(updates=updates)

    async def revoke(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        relation: str,
        subject_type: str,
        subject_id: Union[str, int],
        subject_relation: str = "",
    ) -> None:
        return await self.update(
            updates=[
                RelationUpdateRequest(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    relation=relation,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    update_type=RelationUpdateType.revoke,
                    subject_relation=subject_relation,
                ),
            ]
        )

    async def revoke_many(
        self,
        updates: Sequence[RelationUpdateRevokeRequest],
    ) -> None:
        return await self.update(updates=updates)

    @abstractmethod
    async def update(self, updates: Sequence[RelationUpdateRequest]) -> None:
        raise NotImplementedError()

    async def relations(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        subject_type: str,
        subject_id: Union[str, int],
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[str]:
        """All relationships between the subject and a specific resource.

        Zanzibar example: `program:1#*@user:1`
        Example: `{program:1, user:1} -> [owner, reviewer]`
        """
        return [
            relation
            async for relation in self.relations_generator(
                resource_type=resource_type,
                resource_id=resource_id,
                subject_type=subject_type,
                subject_id=subject_id,
                limit=limit,
                cursor=cursor,
            )
        ]

    @abstractmethod
    def relations_generator(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        subject_type: str,
        subject_id: Union[str, int],
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """All relationships between the subject and a specific resource.

        Zanzibar example: `program:1#*@user:1`
        Example: `{program:1, user:1} -> [owner, reviewer]`
        """
        raise NotImplementedError()

    @abstractmethod
    async def check_relation(
        self,
        resource_type: str,
        resource_id: str | int,
        relation: str,
        subject_type: str,
        subject_id: str | int,
    ) -> bool:
        """Check relation between the subject and a specific resource.

        Zanzibar example: `program:1 relation user:1`
        Example: `{program:1 relation user:1} -> {program:1 relation user:1}`
        """
        raise NotImplementedError()

    async def resources(
        self,
        resource_type: str,
        permission: str,
        subject_type: str,
        subject_id: Union[str, int],
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[str]:
        """IDs for all resources of a given resource_type that have permission for the subject.

        Zanzibar example: `program:*#owner@user:1`
        Example: `{program, user:1, can_edit} -> [program:1, program:3, program:4]`
        """
        return [
            resource
            async for resource in self.resources_generator(
                resource_type=resource_type,
                permission=permission,
                subject_type=subject_type,
                subject_id=subject_id,
                limit=limit,
                cursor=cursor,
            )
        ]

    @abstractmethod
    def resources_generator(
        self,
        resource_type: str,
        permission: str,
        subject_type: str,
        subject_id: Union[str, int],
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """IDs for all resources of a given resource_type that have permission for the subject.

        Zanzibar example: `program:*#owner@user:1`
        Example: `{program, user:1, can_edit} -> [program:1, program:3, program:4]`
        """
        raise NotImplementedError()

    @abstractmethod
    async def resources_many(
        self,
        requests: list[ResourcesRequest],
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[ResourcesRequest, list[str]]:
        raise NotImplementedError()

    async def subjects(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        permission: str,
        subject_type: str,
        full_consistent: bool = False,
    ) -> list[str]:
        """The IDs of all subjects who have this permission for specific resource.

        Zanzibar example: `program:1#owner@user
        Example: `{program:1, can_edit} -> {user:1, user:3, user:4}`
        """
        return [
            subject
            async for subject in self.subjects_generator(
                resource_type=resource_type,
                resource_id=resource_id,
                permission=permission,
                subject_type=subject_type,
                full_consistent=full_consistent,
            )
        ]

    @abstractmethod
    def subjects_generator(
        self,
        resource_type: str,
        resource_id: Union[str, int],
        permission: str,
        subject_type: str,
        full_consistent: bool = False,
    ) -> AsyncGenerator[str, None]:
        """The IDs of all subjects who have this permission for specific resource.

        Zanzibar example: `program:1#owner@user:*`
        Example: `{program:1, can_edit} -> {user:1, user:3, user:4}`
        """
        raise NotImplementedError()

    async def resources_with_relations(
        self,
        resource_type: str,
        subject_type: str,
        subject_id: Union[str, int],
        relation: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ResourcesWithRelations]:
        """IDs and relations list for all resources of a given resource_type and the subject.

        Example: `program:*#*@user:1`
        """
        return [
            resource
            async for resource in self.resources_with_relations_generator(
                resource_type=resource_type,
                subject_type=subject_type,
                subject_id=subject_id,
                relation=relation,
                limit=limit,
                cursor=cursor,
            )
        ]

    @abstractmethod
    def resources_with_relations_generator(
        self,
        resource_type: str,
        subject_type: str,
        subject_id: Union[str, int],
        relation: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncGenerator[ResourcesWithRelations, None]:
        """IDs and relations list for all resources of a given resource_type and the subject.

        Example: `program:*#*@user:1`
        """
        raise NotImplementedError()

    async def subjects_with_relations(
        self,
        resource_type: str,
        resource_id: Union[str, int, None] = None,
        subject_type: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[SubjectsWithRelations]:
        """ID of all subjects and lists of their relations for a specific resource.

        Example: `program:1#*@user:*`
        """
        return [
            subject
            async for subject in self.subjects_with_relations_generator(
                resource_type=resource_type,
                resource_id=resource_id,
                subject_type=subject_type,
                limit=limit,
                cursor=cursor,
            )
        ]

    @abstractmethod
    def subjects_with_relations_generator(
        self,
        resource_type: str,
        resource_id: Union[str, int, None] = None,
        subject_type: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> AsyncGenerator[SubjectsWithRelations, None]:
        """ID of all subjects and lists of their relations for a specific resource.

        Example: `program:1#*@user:*`
        """
        raise NotImplementedError()
