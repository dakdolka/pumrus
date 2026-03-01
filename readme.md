## Request flow diagrams

<table>
<tr>
<td>

<strong>Получение теории</strong>

```mermaid
flowchart TB
    Client[Client]

    Client --> GET_THEORY[GET /api/theory/get_theory]

    GET_THEORY --> Router[router.py
endpoint get_theory]
    Router --> Schemas_Resp[schemas.py
TheoryResponse
TheoryBlockResponse]

    Router --> UC_GetTheory[GetTheoryByIdUseCase]

    UC_GetTheory --> Domain_Theory[entities.py
Theory
TheoryBlock]
    UC_GetTheory --> RepoPort[repository.py
ITheoryRepository]

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Theory[models.py
TheoryBD
TheoryBlockBD]
    Orm_Theory --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Theory
    Orm_Theory --> RepoImpl
    RepoImpl --> UC_GetTheory
    UC_GetTheory --> Router
    Router --> Client
</td> <td>
<strong>Создание теории</strong>

text
flowchart TB
    Client[Client]

    Client --> POST_THEORY[POST /api/theory]

    POST_THEORY --> Router[router.py
endpoint create_theory]
    Router --> Schemas_Req[schemas.py
TheoryCreateRequest]

    Router --> UC_CreateTheory[CreateTheoryBaseUseCase]

    UC_CreateTheory --> Domain_Create[entities.py
Theory]
    UC_CreateTheory --> DomainEnums[enums.py
TheorySubject
TheoryType]
    UC_CreateTheory --> RepoPort[repository.py
ITheoryRepository]

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Create[models.py
TheoryBD
theory2theory_type]
    Orm_Create --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Create
    Orm_Create --> RepoImpl
    RepoImpl --> UC_CreateTheory
    UC_CreateTheory --> Router
    Router --> Client
</td> </tr> <tr> <td>
<strong>Блоки теории</strong>

text
flowchart TB
    Client[Client]

    Client --> POST_BLOCK[POST /api/theory/theory_id/blocks]
    Client --> PUT_BLOCK[PUT /api/theory/blocks/block_id]
    Client --> DELETE_BLOCK[DELETE /api/theory/blocks/block_id]

    POST_BLOCK --> Router[router.py
block endpoints]
    PUT_BLOCK --> Router
    DELETE_BLOCK --> Router

    Router --> Schemas_Block[schemas.py
TheoryBlockCreateRequest]

    Router --> UC_CreateBlock[CreateTheoryBlockUseCase]
    Router --> UC_UpdateBlock[UpdateTheoryBlockUseCase]
    Router --> UC_DeleteBlock[DeleteTheoryBlockUseCase]

    UC_CreateBlock --> Domain_Block[entities.py
TheoryBlock
Theory]
    UC_UpdateBlock --> Domain_Block
    UC_DeleteBlock --> Domain_Block

    UC_CreateBlock --> RepoPort[repository.py
ITheoryRepository]
    UC_UpdateBlock --> RepoPort
    UC_DeleteBlock --> RepoPort

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Block[models.py
TheoryBlockBD
parent and children]
    Orm_Block --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Block
    Orm_Block --> RepoImpl
    RepoImpl --> UC_CreateBlock
    RepoImpl --> UC_UpdateBlock
    RepoImpl --> UC_DeleteBlock

    UC_CreateBlock --> Router
    UC_UpdateBlock --> Router
    UC_DeleteBlock --> Router
    Router --> Client
</td> <td>
<strong>Задания по предмету</strong>

text
flowchart TB
    Client[Client]

    Client --> GET_TASKS_SUBJ[GET /api/theory/get_tasks_theory_for_subject]

    GET_TASKS_SUBJ --> Router[router.py
endpoint get_tasks_theory_for_subject]

    Router --> UC_GetTasksSubj[GetAllTaskTheoryGroupsForSubjectUseCase]

    UC_GetTasksSubj --> Domain_Tasks[entities.py
TaskTheoryGroup
TaskTheory
TaskTheoryWithOrder]
    UC_GetTasksSubj --> RepoPort[repository.py
ITheoryRepository]

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Tasks[models.py
TaskTheoryGroupBD
TaskTheoryBD
TaskTheoryAssociation]
    Orm_Tasks --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Tasks
    Orm_Tasks --> RepoImpl
    RepoImpl --> UC_GetTasksSubj
    UC_GetTasksSubj --> Router
    Router --> Client
</td> </tr> <tr> <td>
<strong>Группы заданий</strong>

text
flowchart TB
    Client[Client]

    Client --> POST_GROUP[POST /api/theory/task-groups]
    Client --> PUT_GROUP[PUT /api/theory/task-groups/group_id]
    Client --> DELETE_GROUP[DELETE /api/theory/task-groups/group_id]

    POST_GROUP --> Router[router.py
task group endpoints]
    PUT_GROUP --> Router
    DELETE_GROUP --> Router

    Router --> UC_CreateGroup[CreateTaskTheoryGroupUseCase]
    Router --> UC_UpdateGroup[UpdateTaskTheoryGroupUseCase]
    Router --> UC_DeleteGroup[DeleteTaskTheoryGroupUseCase]

    UC_CreateGroup --> Domain_Group[entities.py
TaskTheoryGroup]
    UC_UpdateGroup --> Domain_Group
    UC_DeleteGroup --> Domain_Group

    UC_CreateGroup --> RepoPort[repository.py
ITheoryRepository]
    UC_UpdateGroup --> RepoPort
    UC_DeleteGroup --> RepoPort

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Group[models.py
TaskTheoryGroupBD]
    Orm_Group --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Group
    Orm_Group --> RepoImpl
    RepoImpl --> UC_CreateGroup
    RepoImpl --> UC_UpdateGroup
    RepoImpl --> UC_DeleteGroup

    UC_CreateGroup --> Router
    UC_UpdateGroup --> Router
    UC_DeleteGroup --> Router
    Router --> Client
</td> <td>
<strong>Задания и связи с теориями</strong>

text
flowchart TB
    Client[Client]

    Client --> POST_TASK[POST /api/theory/task-groups/group_id/tasks]
    Client --> PUT_TASK[PUT /api/theory/tasks/task_id]
    Client --> DELETE_TASK[DELETE /api/theory/tasks/task_id]
    Client --> PUT_TASK_THEORIES[PUT /api/theory/tasks/task_id/theories]

    POST_TASK --> Router[router.py
task endpoints]
    PUT_TASK --> Router
    DELETE_TASK --> Router
    PUT_TASK_THEORIES --> Router

    Router --> UC_CreateTask[CreateTaskTheoryUseCase]
    Router --> UC_UpdateTask[UpdateTaskTheoryUseCase]
    Router --> UC_DeleteTask[DeleteTaskTheoryUseCase]
    Router --> UC_UpdateTaskLinks[UpdateTaskTheoryLinksUseCase]

    UC_CreateTask --> Domain_Task[entities.py
TaskTheory
TaskTheoryWithOrder]
    UC_UpdateTask --> Domain_Task
    UC_DeleteTask --> Domain_Task
    UC_UpdateTaskLinks --> Domain_Task

    UC_CreateTask --> RepoPort[repository.py
ITheoryRepository]
    UC_UpdateTask --> RepoPort
    UC_DeleteTask --> RepoPort
    UC_UpdateTaskLinks --> RepoPort

    RepoPort --> RepoImpl[repository_impl.py
TheoryRepositoryImpl]
    RepoImpl --> Orm_Task[models.py
TaskTheoryBD
TaskTheoryAssociation]
    Orm_Task --> DbCore[db.py
AsyncSession
MySQL]

    DbCore --> Orm_Task
    Orm_Task --> RepoImpl
    RepoImpl --> UC_CreateTask
    RepoImpl --> UC_UpdateTask
    RepoImpl --> UC_DeleteTask
    RepoImpl --> UC_UpdateTaskLinks

    UC_CreateTask --> Router
    UC_UpdateTask --> Router
    UC_DeleteTask --> Router
    UC_UpdateTaskLinks --> Router
    Router --> Client
</td> </tr> </table> ```
