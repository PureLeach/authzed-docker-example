import asyncio
from enum import StrEnum
from authzed_grpc import AuthzedGrpc
from models import CheckRequest


class Resource(StrEnum):
    battle = "game_portal/battle"


class Subject(StrEnum):
    user = "user"


class BattleRelation(StrEnum):
    hacker = "solo_attacker"
    defender = "solo_defender"


async def add_solo_hacker(client: AuthzedGrpc, battle_id, user_id, role):
    await client.grant(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        relation=role,
        subject_type=Subject.user,
        subject_id=str(user_id),
    )


async def add_solo_defender(client: AuthzedGrpc, battle_id, user_id, role):
    await client.grant(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        relation=role,
        subject_type=Subject.user,
        subject_id=str(user_id),
    )


async def remove_solo_hacker(client: AuthzedGrpc, battle_id, user_id, role):
    await client.revoke(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        relation=role,
        subject_type=Subject.user,
        subject_id=str(user_id),
    )


async def remove_solo_defender(client: AuthzedGrpc, battle_id, user_id, role):
    await client.revoke(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        relation=role,
        subject_type=Subject.user,
        subject_id=str(user_id),
    )


async def get_subjects_with_relations(client: AuthzedGrpc, battle_id):
    subjects_with_relations = await client.subjects_with_relations(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        subject_type=Subject.user,
    )
    print(
        f"\033[31m subjects_with_relations, { subjects_with_relations }, {type(subjects_with_relations)} \033[0m"
    )


async def check_permission(client: AuthzedGrpc, battle_id, user_id, permission):
    result_check = await client.check(
        CheckRequest(
            resource_type=Resource.battle,
            resource_id=str(battle_id),
            subject_type=Subject.user,
            subject_id=str(user_id),
            permission=permission,
        )
    )
    print(f"\033[31m result_check, { result_check }, {type(result_check)} \033[0m")


async def check_relation(client: AuthzedGrpc, battle_id, user_id, role):
    result_check = await client.check_relation(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        relation=role,
        subject_type=Subject.user,
        subject_id=str(user_id),
    )
    print(f"\033[31m result_check, { result_check }, {type(result_check)} \033[0m")


async def get_resources_with_relations(client: AuthzedGrpc, user_id, role):
    resources_with_relations = await client.resources_with_relations(
        resource_type=Resource.battle,
        subject_type=Subject.user,
        subject_id=str(user_id),
        relation=role,
    )
    print(
        f"\033[31m resources_with_relations, { resources_with_relations }, {type(resources_with_relations)} \033[0m"
    )


async def get_relations_by_id(client: AuthzedGrpc, battle_id, user_id):
    relations = await client.relations(
        resource_type=Resource.battle,
        resource_id=str(battle_id),
        subject_type=Subject.user,
        subject_id=str(user_id),
    )
    print(f"\033[31m relations, { relations }, {type(relations)} \033[0m")


async def main():
    client = AuthzedGrpc(target="localhost:50052", token="token", allow_insecure=True)
    battle_id = 1
    user_one_id = 1
    user_two_id = 2

    await add_solo_hacker(client, battle_id, user_one_id, BattleRelation.hacker)
    await add_solo_defender(client, battle_id, user_two_id, BattleRelation.defender)

    await remove_solo_hacker(client, battle_id, user_one_id, BattleRelation.defender)
    await remove_solo_defender(client, battle_id, user_two_id, BattleRelation.defender)

    await get_resources_with_relations(client, user_one_id, BattleRelation.hacker)
    await get_subjects_with_relations(client, battle_id)
    await get_relations_by_id(client, battle_id, user_one_id)

    await check_permission(client, battle_id, user_one_id, "battle_view")
    await check_relation(client, battle_id, user_one_id, BattleRelation.hacker)


if __name__ == "__main__":
    asyncio.run(main())
