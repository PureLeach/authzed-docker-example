import asyncio
from collections import defaultdict
from typing import AsyncGenerator, Iterable

from authzed.api.v1 import (
    BulkCheckPermissionRequest,
    BulkCheckPermissionRequestItem,
    CheckPermissionRequest,
    CheckPermissionResponse,
    Consistency,
    ExpandPermissionTreeRequest,
    LookupResourcesRequest,
    ObjectReference,
    ReadRelationshipsRequest,
    RelationshipFilter,
    SubjectFilter,
    SubjectReference,
    WriteRelationshipsRequest,
)
from authzed.api.v1.core_pb2 import Cursor, Relationship, RelationshipUpdate
from grpcutil import bearer_token_credentials, insecure_bearer_token_credentials
from authzed.api.v1 import AsyncClient
from authzed_base import BaseAuthzed
from models import (
    Access,
    CheckRequest,
    RelationUpdateRequest,
    RelationUpdateType,
    ResourcesRequest,
    ResourcesWithRelations,
    SubjectsWithRelations,
)


class AuthzedGrpc(BaseAuthzed):
    def __init__(
        self,
        target: str,
        token: str,
        allow_insecure: bool = False,
    ):
        """
        GRPC client for Authzed.

        The client uses a secure connection by default. The location of the certificate is specified in a variable
        GRPC_DEFAULT_SSL_ROOTS_FILE_PATH.
        GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/ca/authzed_spicedb_ca.pem by default.

        :param target: URI for spicedb grpc server. Like authzed_spicedb:50051
        :param token: Auth token
        :param allow_insecure: Allow insecure connection for spicedb grpc server. Only for localhost.
        """
        super().__init__()
        self.target = target
        self.token = token

        self.client = AsyncClient(
            target=self.target,
            credentials=insecure_bearer_token_credentials(token)
            if allow_insecure
            else bearer_token_credentials(token),
        )

    async def is_allowed(
        self,
        request: CheckRequest,
        **kwargs,
    ) -> bool:
        check_result = await self.check(
            request=request,
            **kwargs,
        )
        return check_result.is_allowed()

    async def check(
        self,
        request: CheckRequest,
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> Access:
        subject_reference = SubjectReference(
            object=ObjectReference(
                object_type=request.subject_type,
                object_id=str(request.subject_id),
            ),
        )

        # see more about consistency levels at https://authzed.com/docs/spicedb/concepts/consistency#levels
        if full_consistent:
            consistency = Consistency(fully_consistent=True)
        elif minimize_latency:
            consistency = Consistency(minimize_latency=True)
        else:
            consistency = None

        check_permission_request = CheckPermissionRequest(
            resource=ObjectReference(
                object_type=request.resource_type, object_id=str(request.resource_id)
            ),
            permission=request.permission,
            subject=subject_reference,
            consistency=consistency,
        )

        response = await self.client.CheckPermission(check_permission_request)

        if (
            response.permissionship
            == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
        ):
            return Access.allow
        else:
            return Access.forbid

    async def check_many(
        self,
        requests: list[CheckRequest],
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> dict[CheckRequest, Access]:
        if not requests:
            return {}

        bulk_check_permission_request: list[BulkCheckPermissionRequestItem] = []

        for request in requests:
            object_reference = ObjectReference(
                object_type=request.resource_type,
                object_id=str(request.resource_id),
            )
            subject_reference = SubjectReference(
                object=ObjectReference(
                    object_type=request.subject_type,
                    object_id=str(request.subject_id),
                ),
            )
            bulk_check_permission_request_item = BulkCheckPermissionRequestItem(
                resource=object_reference,
                permission=request.permission,
                subject=subject_reference,
            )
            bulk_check_permission_request.append(bulk_check_permission_request_item)

        # see more about consistency levels at https://authzed.com/docs/spicedb/concepts/consistency#levels
        if full_consistent:
            consistency = Consistency(fully_consistent=True)
        elif minimize_latency:
            consistency = Consistency(minimize_latency=True)
        else:
            consistency = None

        response = await self.client.BulkCheckPermission(
            BulkCheckPermissionRequest(
                consistency=consistency,
                items=bulk_check_permission_request,
            )
        )

        result_response = {
            check: Access.forbid for check in requests
        }  # forbid by default
        for check_result in response.pairs:
            if (
                check_result.item.permissionship
                == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
            ):
                object_id = check_result.request.resource.object_id
                subject_id = check_result.request.subject.object.object_id
                check_request = CheckRequest(
                    resource_type=check_result.request.resource.object_type,
                    resource_id=object_id,
                    subject_id=subject_id,
                    subject_type=check_result.request.subject.object.object_type,
                    permission=check_result.request.permission,
                )
                result_response[check_request] = Access.allow

        return result_response

    async def is_allowed_many(
        self,
        requests: list[CheckRequest],
        full_consistent: bool = False,
        minimize_latency: bool = False,
    ) -> dict[CheckRequest, bool]:
        results_list = await self.check_many(
            requests=requests,
            full_consistent=full_consistent,
            minimize_latency=minimize_latency,
        )
        return {
            request: response.is_allowed() for request, response in results_list.items()
        }

    async def update(
        self,
        updates: list[RelationUpdateRequest],
    ) -> None:
        relationship_updates = []
        for update in updates:
            if update.update_type is None:
                raise ValueError("update_type cannot be None")
            relationship_update = RelationshipUpdate(
                operation=self._relation_update_type(update.update_type),
                relationship=Relationship(
                    resource=ObjectReference(
                        object_type=update.resource_type,
                        object_id=str(update.resource_id),
                    ),
                    relation=update.relation,
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type=update.subject_type,
                            object_id=str(update.subject_id),
                        ),
                        optional_relation=update.subject_relation,
                    ),
                ),
            )
            relationship_updates.append(relationship_update)

        request = WriteRelationshipsRequest(updates=relationship_updates)
        response = await self.client.WriteRelationships(request=request)
        try:
            _ = response.written_at.token
        except AttributeError:
            raise RuntimeError("Invalid authzed response.")

    async def relations_generator(
        self,
        resource_type: str,
        resource_id: str | int,
        subject_type: str,
        subject_id: str | int,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncGenerator[str, None]:
        subject_filter = SubjectFilter(
            subject_type=subject_type, optional_subject_id=str(subject_id)
        )
        relationship_filter = RelationshipFilter(
            resource_type=resource_type,
            optional_subject_filter=subject_filter,
            optional_resource_id=str(resource_id),
        )

        relationship_request = ReadRelationshipsRequest(
            relationship_filter=relationship_filter,
            optional_cursor=Cursor(token=cursor) if cursor else None,
        )

        if limit:
            relationship_request.optional_limit = limit

        async for item in self.client.ReadRelationships(relationship_request):
            yield item.relationship.relation

    async def check_relation(
        self,
        resource_type: str,
        resource_id: str | int,
        relation: str,
        subject_type: str,
        subject_id: str | int,
    ) -> bool:
        subject_filter = SubjectFilter(
            subject_type=subject_type, optional_subject_id=str(subject_id)
        )

        relationship_filter = RelationshipFilter(
            resource_type=resource_type,
            optional_resource_id=str(resource_id),
            optional_relation=relation,
            optional_subject_filter=subject_filter,
        )

        relationship_request = ReadRelationshipsRequest(
            relationship_filter=relationship_filter
        )

        async for relationship in self.client.ReadRelationships(
            request=relationship_request
        ):
            if relationship.relationship.relation == relation:
                return True

        return False

    async def resources_generator(
        self,
        resource_type: str,
        permission: str,
        subject_type: str,
        subject_id: str | int,
        limit: int  = 0,
        cursor: str | None = None,
    ) -> AsyncGenerator[str, None]:
        subject_reference = SubjectReference(
            object=ObjectReference(
                object_type=subject_type,
                object_id=str(subject_id),
            ),
        )

        requests = LookupResourcesRequest(
            resource_object_type=resource_type,
            permission=permission,
            subject=subject_reference,
            optional_limit=limit,
            optional_cursor=Cursor(token=cursor) if cursor else None,
        )

        stream_call = self.client.LookupResources(requests)
        async for item in stream_call:
            yield item.resource_object_id

    async def resources_many(
        self,
        requests: list[ResourcesRequest],
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[ResourcesRequest, list[str]]:
        """
        So far frontend used check_many to check if user has rights to access object of some type.
        But if there are 50 objects of one type (e.g. battles), frontend sent 50 requests to check if user can see
        this object. All of this - just to know if user has a right to access at least one object.
        So now we decided to try next behavior: frontend requests if user has at least one object with chosen privilege,
        so number of requests will be not
            N * M
        where N is number of objects, and M - number of possible privileges, but
            M
        where number of resource requests depends only on number of privileges checked.
        It uses old-style asyncio-batching, but number of parallel requests here must be much lower compared to the
        old check_many.
        By the moment of this written, we will exchange 1 request with ~1000 checks on ~25 parallel requests
        (each fetches maximum 1 item), so we will know which decision is more optimal.
        Good thing here is that number of privileges grows not so fast as number of objects,
        so I hope we will be ok with it.
        """
        tasks = {
            request: asyncio.create_task(
                self.resources(
                    resource_type=request.resource_type,
                    permission=request.permission,
                    subject_type=request.subject_type,
                    subject_id=request.subject_id,
                    limit=limit,
                    cursor=cursor,
                )
            )
            for request in requests
        }

        if tasks:
            try:
                await asyncio.wait(
                    tasks.values(),
                    return_when=asyncio.ALL_COMPLETED,
                    timeout=10,
                )
            except asyncio.TimeoutError:
                self.logger.error("Authzed resources many timeout error.")

        result = {}
        for request, task in tasks.items():
            if not task.done():
                self.logger.error("Authzed resources request task not finished.")
                task.cancel()
                result[request] = []
            elif task.exception() is not None:
                self.logger.error(task.exception())
                result[request] = []
            else:
                result[request] = task.result()

        return result

    async def subjects_generator(
        self,
        resource_type: str,
        resource_id: str | int,
        permission: str,
        subject_type: str,
        full_consistent: bool = False,
    ) -> AsyncGenerator[str, None]:
        expand_permission_tree_request = ExpandPermissionTreeRequest(
            resource=ObjectReference(
                object_type=resource_type, object_id=str(resource_id)
            ),
            permission=permission,
            consistency=Consistency(fully_consistent=True) if full_consistent else None,
        )

        permission_tree_response = await self.client.ExpandPermissionTree(
            request=expand_permission_tree_request
        )

        try:
            for subject_id in self._parse_subjects(
                permission_tree_response.tree_root,
                subject_type=subject_type,
            ):
                yield subject_id
        except AttributeError:
            raise RuntimeError("Invalid permissions expand response.")

    async def resources_with_relations_generator(
        self,
        resource_type: str,
        subject_type: str,
        subject_id: str | int,
        relation: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncGenerator[ResourcesWithRelations, None]:
        subject_filter = SubjectFilter(
            subject_type=subject_type, optional_subject_id=str(subject_id)
        )
        relationship_filter = RelationshipFilter(
            resource_type=resource_type, optional_subject_filter=subject_filter
        )

        if relation:
            relationship_filter.optional_relation = relation

        relationship_request = ReadRelationshipsRequest(
            relationship_filter=relationship_filter,
            optional_cursor=Cursor(token=cursor) if cursor else None,
        )

        if limit:
            relationship_request.optional_limit = limit

        resources_with_relations = defaultdict(set)

        async for item in self.client.ReadRelationships(relationship_request):
            object_id = item.relationship.resource.object_id
            resources_with_relations[object_id].add(item.relationship.relation)

        for object_id, relations in resources_with_relations.items():
            yield ResourcesWithRelations(
                resource_id=object_id, relations=list(relations)
            )

    async def subjects_with_relations_generator(
        self,
        resource_type: str,
        resource_id: str | int | None = None,
        subject_type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncGenerator[SubjectsWithRelations, None]:
        relationship_filter = RelationshipFilter(
            resource_type=resource_type,
            optional_subject_filter=SubjectFilter(subject_type=subject_type)
            if subject_type
            else None,
        )

        if resource_id:
            relationship_filter.optional_resource_id = str(resource_id)

        relationship_request = ReadRelationshipsRequest(
            relationship_filter=relationship_filter,
            optional_cursor=Cursor(token=cursor) if cursor else None,
        )

        if limit:
            relationship_request.optional_limit = limit

        subject_with_relations = defaultdict(set)

        async for item in self.client.ReadRelationships(relationship_request):
            subject = (
                item.relationship.subject.object.object_type,
                item.relationship.subject.object.object_id,
            )
            subject_with_relations[subject].add(item.relationship.relation)

        for subject, relations in subject_with_relations.items():
            subject_type, subject_id = subject
            yield SubjectsWithRelations(
                subject_type=subject_type,
                subject_id=subject_id,
                relations=list(relations),
            )

    @staticmethod
    def _relation_update_type(
        update_type: RelationUpdateType,
    ) -> RelationshipUpdate.Operation.ValueType:
        match update_type:
            case RelationUpdateType.grant:
                operation = RelationshipUpdate.Operation.OPERATION_TOUCH
            case RelationUpdateType.revoke:
                operation = RelationshipUpdate.Operation.OPERATION_DELETE
            case _:
                raise NotImplementedError("Relation update type not defined.")
        return operation

    @classmethod
    def _parse_subjects(cls, root, subject_type: str) -> Iterable[str]:
        if hasattr(root, "leaf"):
            yield from [
                subject.object.object_id
                for subject in root.leaf.subjects
                if subject.object.object_type == subject_type
            ]
        if hasattr(root, "intermediate") and hasattr(root.intermediate, "children"):
            for children in root.intermediate.children:
                yield from cls._parse_subjects(children, subject_type=subject_type)
