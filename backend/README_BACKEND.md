# PUMRUS Backend

Бекенд веб-приложения для управления теоретическим материалом и связанными учебными заданиями. Построен на принципах **Domain-Driven Design (DDD)** с использованием FastAPI и асинхронной работы с MySQL.

## 🏗️ Архитектура

Проект следует принципам **Domain-Driven Design (DDD)** с четким разделением на слои и изоляцией бизнес-логики от инфраструктуры.

## 📁 Структура проекта

```
backend/
├── .venv/                          # Виртуальное окружение Python
├── app/                            # Корневая директория приложения
│   ├── api/                        # 🌐 Interface Layer (Presentation)
│   │   └── theory/
│   │       ├── __init__.py
│   │       ├── crud.py             # CRUD операции (опционально)
│   │       ├── router.py           # FastAPI эндпоинты
│   │       ├── schemas.py          # Pydantic DTO схемы
│   │       ├── __init__.py
│   │       └── main.py
│   │
│   ├── core/                       # 🎯 Domain & Application Layer
│   │   ├── theory/                 # Bounded Context: Theory
│   │   │   ├── __init__.py
│   │   │   ├── entities.py         # Domain Entities (доменные сущности)
│   │   │   ├── enums.py            # Domain Value Objects (перечисления)
│   │   │   ├── repository.py       # Repository Interface (абстракция)
│   │   │   ├── use_cases.py        # Application Services (бизнес-логика)
│   │   │   └── __init__.py
│   │   ├── config.py               # Конфигурация приложения
│   │   └── db.py                   # Database session factory
│   │
│   ├── infra/                      # 🔧 Infrastructure Layer
│   │   └── theory/
│   │       ├── __init__.py
│   │       ├── models.py           # SQLAlchemy ORM модели (persistence)
│   │       └── repository_impl.py  # Repository Implementation
│   │
│   └── scripts/                    # 📜 Utility Scripts
│       ├── txts/                   # Текстовые файлы с данными
│       ├── __init__.py
│       ├── create.py               # Инициализация БД
│       └── parse_theory.py         # Парсинг данных (устаревший)
│
├── .env                            # Переменные окружения
├── Dockerfile                      # Docker конфигурация
├── README_BACKEND.md              # Документация
└── requirements.txt                # Python зависимости
```

## 🎨 DDD Architecture Layers

### 1. **Interface Layer** (`app/api/`)
**Роль:** Обработка HTTP запросов, валидация входящих данных, маршрутизация

**Компоненты:**
- `router.py` - FastAPI роуты и эндпоинты
- `schemas.py` - Pydantic модели (DTO) для сериализации/десериализации
- `crud.py` - Опциональный слой CRUD операций

**Ответственность:**
- Принимает HTTP запросы
- Валидирует данные через Pydantic
- Вызывает Use Cases из Application Layer
- Преобразует результаты в HTTP ответы

### 2. **Domain Layer** (`app/core/theory/entities.py`, `enums.py`)
**Роль:** Ядро бизнес-логики, чистые доменные модели без зависимостей

**Компоненты:**
- `entities.py` - Доменные сущности (Entity)
  - `Theory` - Агрегат теории
  - `TheoryBlock` - Value Object/Entity блока
  - `TaskTheory` - Сущность задания
  - `TaskTheoryGroup` - Агрегат группы заданий
- `enums.py` - Value Objects (перечисления)
  - `BlockType` - типы блоков
  - `TheoryType` - типы теории
  - `TheorySubject` - предметы

**Принципы:**
- Инкапсуляция бизнес-правил
- Независимость от фреймворков и БД
- Использование dataclasses для иммутабельности
- Доменные модели описывают бизнес-концепции

### 3. **Application Layer** (`app/core/theory/use_cases.py`)
**Роль:** Оркестрация бизнес-процессов, координация между доменом и инфраструктурой

**Компоненты:**
- Use Cases (Application Services) для каждой операции:
  - `CreateTheoryBaseUseCase` - создание теории
  - `GetTheoryByIdUseCase` - получение теории
  - `CreateTheoryBlockUseCase` - создание блока
  - `UpdateTaskTheoryLinksUseCase` - обновление связей
  - и другие...

**Принципы:**
- Один Use Case = одна бизнес-операция
- Управление транзакциями
- Координация вызовов репозитория
- Не содержит бизнес-логики (она в Domain)

### 4. **Infrastructure Layer** (`app/infra/`)
**Роль:** Реализация технических деталей, персистентность данных

**Компоненты:**
- `models.py` - SQLAlchemy ORM модели
  - `TheoryBD` - таблица theory
  - `TheoryBlockBD` - таблица theory_block
  - `TaskTheoryGroupBD` - таблица task_theory_group
  - Ассоциативные таблицы и связи
- `repository_impl.py` - Реализация Repository Interface
  - CRUD операции с БД
  - Маппинг Domain Entities ↔ ORM Models
  - SQL запросы через SQLAlchemy

**Принципы:**
- Dependency Inversion: зависит от абстракций из Domain
- Технические детали скрыты от верхних слоев
- Persistence Ignorance в Domain Layer

### 5. **Repository Pattern** (`repository.py` + `repository_impl.py`)
**Роль:** Абстракция доступа к данным

- `repository.py` - Интерфейс (ABC) в Domain Layer
- `repository_impl.py` - Реализация в Infrastructure Layer

**Преимущества:**
- Domain не знает о БД
- Легкая замена источника данных
- Тестируемость (mock репозиториев)

## 📚 API Endpoints

### Теория

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/theory/all_theory_for_subject/{subject_id}` | Получить всю теорию по предмету |
| `GET` | `/theory/all_theory_dop_info` | Получить доп. информацию о теории |
| `GET` | `/theory/get_theory/{theory_id}` | Получить конкретную теорию по ID |
| `GET` | `/theory/get_tasks_theory_for_subject/{subject_id}` | Получить задания по предмету |
| `POST` | `/theory/` | Создать новую теорию |
| `PUT` | `/theory/{theory_id}` | Обновить теорию |

### Блоки теории

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/theory/{theory_id}/blocks` | Создать блок теории |
| `PUT` | `/theory/blocks/{block_id}` | Обновить блок |
| `DELETE` | `/theory/blocks/{block_id}` | Удалить блок |

### Группы теории по заданиям

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/theory/task-groups` | Создать группу заданий |
| `PUT` | `/theory/task-groups/{group_id}` | Обновить группу |
| `DELETE` | `/theory/task-groups/{group_id}` | Удалить группу |

### Теория по заданиям

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/theory/task-groups/{group_id}/tasks` | Создать задание |
| `PUT` | `/theory/tasks/{task_id}` | Обновить задание |
| `DELETE` | `/theory/tasks/{task_id}` | Удалить задание |
| `PUT` | `/theory/tasks/{task_id}/theories` | Связать задание с теориями |

## 🗄️ Модель данных (Domain Model)

### Domain Entities

#### Theory (Теория) - Aggregate Root
Содержит теоретический материал, разбитый на иерархические блоки.

**Domain Entity (`entities.py`):**
```python
@dataclass
class Theory:
    name: str
    subj: TheorySubject
    id: Optional[int] = None
    blocks: List[Optional[TheoryBlock]] = field(default_factory=list)
    types: Optional[List[TheoryType]] = field(default_factory=list)
```

**Persistence Model (`models.py`):**
- `TheoryBD` - SQLAlchemy модель с relationships
- Таблица: `theory`
- Связи: many-to-many с `theory_type`, one-to-many с `theory_block`

**Поля:**
- `id` - идентификатор (PK)
- `name` - название теории
- `subject_id` - предмет (FK → theory_subject)
- `types` - типы теории (M2M → theory_type)
- `blocks` - блоки теории (1:M → theory_block)

#### TheoryBlock (Блок теории) - Entity/Value Object
Иерархическая структура с поддержкой неограниченной вложенности.

**Domain Entity:**
```python
@dataclass
class TheoryBlock:
    type: BlockType
    content: str
    order: int
    theory_id: Optional[int] = None
    id: Optional[int] = None
    children: List[Optional["TheoryBlock"]] = field(default_factory=list)
```

**Persistence Model:**
- `TheoryBlockBD` - рекурсивная структура через `parent_id`
- Таблица: `theory_block`
- Self-referencing relationship для parent-children

**Поля:**
- `id` - идентификатор (PK)
- `content` - содержимое блока (TEXT)
- `type` - тип блока (enum: BlockType)
- `theory_id` - теория (FK → theory)
- `parent_id` - родительский блок (FK → theory_block, self-ref)
- `order` - порядок отображения (INT)
- `children` - дочерние блоки (1:M)

**Типы блоков (BlockType enum):**
- `title` - заголовок
- `subtitle` - подзаголовок  
- `rule` - правило
- `example` - пример
- `exception` - исключение
- `important` - важное
- `text` - текст
- `svg` - SVG изображение
- `group` - группа (контейнер для вложенности)
- `link` - ссылка

#### TaskTheoryGroup (Группа заданий) - Aggregate Root
Группировка связанных заданий по темам.

**Domain Entity:**
```python
@dataclass
class TaskTheoryGroup:
    group_name: str
    is_single: bool
    subject: TheorySubject | int
    tasks_theories: Optional[List["TaskTheory"]] = None
    id: Optional[int] = None
```

**Persistence Model:**
- `TaskTheoryGroupBD`
- Таблица: `task_theory_group`

**Поля:**
- `id` - идентификатор (PK)
- `name` - название группы
- `is_single` - флаг единственного активного задания
- `subject_id` - предмет (FK → theory_subject)
- `tasks_theories` - задания в группе (1:M → task_theory)

#### TaskTheory (Задание) - Entity
Задание, связанное с набором теорий.

**Domain Entity:**
```python
@dataclass
class TaskTheory:
    task_name: str
    theories: Optional[List[TaskTheoryWithOrder]] = None
    id: Optional[int] = None
```

**Persistence Model:**
- `TaskTheoryBD`
- Таблица: `task_theory`

**Поля:**
- `id` - идентификатор (PK)
- `name` - название задания
- `group_id` - группа (FK → task_theory_group)
- `theory_associations` - связи с теориями (M2M через association object)

#### TaskTheoryAssociation - Association Object
Связь задания с теориями с поддержкой порядка отображения.

**Domain Entity:**
```python
@dataclass
class TaskTheoryWithOrder:
    theory: Any
    order: int
```

**Persistence Model:**
- `TaskTheoryAssociation`
- Таблица: `task_theory2theory`

**Поля:**
- `theory_id` - теория (FK → theory, PK)
- `task_theory_id` - задание (FK → task_theory, PK)
- `order` - порядок отображения (INT)

**Особенность:** Composite Primary Key + дополнительное поле `order` для упорядочивания теорий в рамках одного задания.

### Value Objects (Enums)

#### TheorySubject - Предметы
```python
class TheorySubject(str, Enum):
    infa = "Информатика"
    rus = "Русский язык"
```

#### TheoryType - Типы теории
```python
class TheoryType(str, Enum):
    # Для русского языка
    speechpart = "Части речи"
    text = "Текст"
    wordparts = "Морфемы"
    punctuation = "Пунктуация"

    # Для информатики
    database = "База данных"
    encoding = "Кодировка"
```

**Связь:** Каждый предмет имеет свой набор типов теории (1:M).

### Референсные таблицы

#### TheorySubjectBD - Предметы
- Таблица: `theory_subject`
- Связи: 1:M с `theory`, `task_theory_group`, `theory_type`

#### TheoryTypeBD - Типы теории
- Таблица: `theory_type`
- Связи: M2M с `theory`, M:1 с `theory_subject`

### Ассоциативные таблицы

#### theory2theory_type
Связь теории с несколькими типами (many-to-many).

```python
theory2theory_type = Table(
    "theory2theory_type",
    Base.metadata,
    Column("theory_id", Integer, ForeignKey("theory.id"), primary_key=True),
    Column("type_id", Integer, ForeignKey("theory_type.id"), primary_key=True),
)
```

## 🔧 Технологический стек

| Технология | Версия | Назначение |
|------------|--------|------------|
| **FastAPI** | latest | Web framework (Interface Layer) |
| **SQLAlchemy** | 2.0+ | ORM с async support (Infrastructure) |
| **asyncmy** | latest | Async MySQL driver |
| **Pydantic** | 2.0+ | Валидация данных (DTO) |
| **Uvicorn** | latest | ASGI server |
| **MySQL** | 8.0+ | Реляционная БД |
| **Python** | 3.10+ | Язык программирования |

## 📝 Детальный анализ компонентов

### 1. Interface Layer (`app/api/theory/`)

#### `router.py` - HTTP Controllers
FastAPI роуты, обрабатывающие HTTP запросы и делегирующие работу Use Cases.

**Паттерн:** Controller → Use Case → Repository

**Пример:**
```python
@router.get("/theory/get_theory/{theory_id}", response_model=TheoryResponse)
async def get_theory(theory_id: int):
    repo = TheoryRepositoryImpl()
    usecase = GetTheoryByIdUseCase(repo)
    theory = await usecase.execute(theory_id)
    if not theory:
        raise HTTPException(status_code=404, detail="Theory not found")
    return theory
```

**Ключевые эндпоинты:**
- **GET** `/all_theory_for_subject/{subject_id}` - список теорий
- **GET** `/get_theory/{theory_id}` - детали теории с блоками
- **POST** `/` - создание теории с типами
- **PUT** `/{theory_id}` - обновление базовой информации
- **POST** `/{theory_id}/blocks` - добавление блока
- **PUT** `/blocks/{block_id}` - обновление блока
- **DELETE** `/blocks/{block_id}` - удаление блока (cascade)
- Группы и задания: полный CRUD

**Особенности:**
- Инстанцирование репозитория в каждом эндпоинте (можно улучшить через DI)
- Валидация через Pydantic schemas
- HTTP error handling (404, 400)

#### `schemas.py` - DTO (Data Transfer Objects)
Pydantic модели для сериализации/десериализации данных между слоями.

**Response Models (API → Client):**
```python
class TheoryResponse(BaseModel):
    id: int
    name: str
    blocks: List[TheoryBlockResponse]

class TheoryBlockResponse(BaseModel):
    id: int
    type: BlockType
    content: str
    order: int
    parent_id: Optional[int] = None
    theory_id: Optional[int] = None
    children: List["TheoryBlockResponse"] = []  # Рекурсивная структура
```

**Request Models (Client → API):**
```python
class TheoryCreateRequest(BaseModel):
    name: str
    subject: TheorySubject
    type_ids: list[int]

class TheoryBlockCreateRequest(BaseModel):
    type: BlockType
    content: str
    parent_id: Optional[int] = None
    order: int
```

**Особенности:**
- Вложенные модели для иерархических структур
- Optional поля для PATCH операций
- Валидация enum значений
- Field описания для документации

### 2. Domain Layer (`app/core/theory/`)

#### `entities.py` - Domain Entities
Чистые доменные модели, описывающие бизнес-концепции без технических деталей.

**Принципы:**
- Использование `@dataclass` для простоты
- Иммутабельность данных (frozen=False для гибкости)
- Отсутствие зависимостей от frameworks
- Богатая доменная модель (если добавить методы)

**Агрегаты:**
- `Theory` - корень агрегата теории
- `TaskTheoryGroup` - корень агрегата заданий

**Entities:**
- `TheoryBlock` - может быть Entity или Value Object
- `TaskTheory` - сущность задания

**Value Objects:**
- `TheoryType`, `TheorySubject` - в enums
- `TaskTheoryWithOrder` - значение с порядком

**Пример богатой модели (можно добавить):**
```python
@dataclass
class Theory:
    name: str
    subj: TheorySubject
    blocks: List[TheoryBlock] = field(default_factory=list)

    def add_block(self, block: TheoryBlock) -> None:
        """Бизнес-логика добавления блока"""
        block.order = len(self.blocks)
        self.blocks.append(block)

    def validate(self) -> bool:
        """Доменная валидация"""
        return len(self.name) > 0 and self.subj is not None
```

#### `enums.py` - Value Objects
Перечисления для строгой типизации доменных концепций.

```python
class BlockType(str, Enum):
    title = "title"
    subtitle = "subtitle"
    rule = "rule"
    example = "example"
    exception = "exception"
    important = "important"
    text = "text"
    svg = "svg"
    group = "group"  # Специальный тип для группировки
    link = "link"
```

**Преимущества:**
- Type safety
- Автодополнение в IDE
- Централизованное управление допустимыми значениями

#### `repository.py` - Repository Interface
Абстрактный интерфейс (порт) для доступа к данным.

```python
class ITheoryRepository(ABC):
    async def create_theory(self, session: AsyncSession, 
                           theory: Theory, subject) -> int: ...

    async def get_theory_by_id(self, session: AsyncSession, 
                               id: int) -> Theory: ...

    async def get_all_theories_for_subject(self, session: AsyncSession, 
                                          subject_id: int) -> List[tuple[int, str]]: ...
    # ... другие методы
```

**Принципы:**
- Абстрактный класс (ABC)
- Методы оперируют Domain Entities
- Не содержит реализации
- Определяет контракт персистентности

#### `use_cases.py` - Application Services
Оркестрация бизнес-процессов и координация взаимодействия.

**Структура Use Case:**
```python
class CreateTheoryBlockUseCase:
    def __init__(self, repo: ITheoryRepository):
        self.repo = repo

    async def execute(self, theory_id: int, type: BlockType, 
                     content: str, parent_id: Optional[int], order: int):
        async with async_session_factory() as session:
            async with session.begin():
                return await self.repo.create_block(
                    session, theory_id, type, content, parent_id, order
                )
```

**Каталог Use Cases:**

**Theory Management:**
- `CreateTheoryBaseUseCase` - создание теории
- `UpdateTheoryBaseUseCase` - обновление метаданных
- `GetTheoryByIdUseCase` - получение с eager loading
- `GetAllTheoriesForSubjectUseCase` - список по предмету
- `GetAllTheoryDopInfoUseCase` - дополнительная информация

**Theory Blocks:**
- `CreateTheoryBlockUseCase` - добавление блока
- `UpdateTheoryBlockUseCase` - изменение блока
- `DeleteTheoryBlockUseCase` - удаление (cascade)

**Task Theory Groups:**
- `CreateTaskTheoryGroupUseCase` - создание группы
- `UpdateTaskTheoryGroupUseCase` - обновление группы
- `DeleteTaskTheoryGroupUseCase` - удаление группы
- `GetAllTaskTheoryGroupsForSubjectUseCase` - получение с заданиями

**Task Theories:**
- `CreateTaskTheoryUseCase` - создание задания
- `UpdateTaskTheoryUseCase` - обновление задания
- `DeleteTaskTheoryUseCase` - удаление задания
- `UpdateTaskTheoryLinksUseCase` - связывание с теориями

**Utility:**
- `CreateTheoryTypesAndSubjsUseCase` - инициализация справочников
- `GetTheoriesByNamesUseCase` - поиск по именам

**Принципы:**
- Single Responsibility - один use case = одна операция
- Управление транзакциями через context managers
- Зависимость от Repository Interface (DI)
- Не содержит бизнес-логики (она в Domain)

### 3. Infrastructure Layer (`app/infra/theory/`)

#### `models.py` - ORM Models (Persistence)
SQLAlchemy модели для маппинга доменных сущностей на реляционную БД.

**Особенности реализации:**

**1. Иерархические структуры (Self-referencing):**
```python
class TheoryBlockBD(Base):
    __tablename__ = "theory_block"

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theory_block.id", ondelete="CASCADE"), 
        nullable=True
    )

    children: Mapped[List["TheoryBlockBD"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="TheoryBlockBD.order"
    )

    parent: Mapped[Optional["TheoryBlockBD"]] = relationship(
        back_populates="children", 
        remote_side=[id]  # Указание "родительской" стороны
    )
```

**2. Many-to-Many с Association Object:**
```python
class TaskTheoryAssociation(Base):
    __tablename__ = "task_theory2theory"

    theory_id: Mapped[int] = mapped_column(
        ForeignKey("theory.id"), primary_key=True
    )
    task_theory_id: Mapped[int] = mapped_column(
        ForeignKey("task_theory.id"), primary_key=True
    )
    order: Mapped[int] = mapped_column(default=0)  # Дополнительный атрибут

    # Bidirectional relationships
    theory: Mapped["TheoryBD"] = relationship(back_populates="task_associations")
    task: Mapped["TaskTheoryBD"] = relationship(back_populates="theory_associations")
```

**3. Простая Many-to-Many (через Table):**
```python
theory2theory_type = Table(
    "theory2theory_type",
    Base.metadata,
    Column("theory_id", Integer, ForeignKey("theory.id"), primary_key=True),
    Column("type_id", Integer, ForeignKey("theory_type.id"), primary_key=True),
)
```

**4. Cascade операции:**
```python
blocks: Mapped[list["TheoryBlockBD"]] = relationship(
    back_populates='theory',
    cascade="all, delete-orphan"  # При удалении теории удаляются все блоки
)
```

**Таблицы:**
- `theory` - основная таблица теорий
- `theory_block` - блоки с self-join
- `theory_subject` - справочник предметов
- `theory_type` - справочник типов теории
- `task_theory_group` - группы заданий
- `task_theory` - задания
- `theory2theory_type` - связка теории и типов
- `task_theory2theory` - связка заданий и теорий с порядком

#### `repository_impl.py` - Repository Implementation
Конкретная реализация Repository Interface с использованием SQLAlchemy.

**Ключевые методы:**

**1. Создание с рекурсией:**
```python
async def create_theory(self, session: AsyncSession, 
                       theory: Theory, subj: TheorySubject | None) -> int:
    # Маппинг Domain Entity → ORM Model
    bd_theory = TheoryBD(types=types, subject_id=subj.id, name=theory.name)
    session.add(bd_theory)

    # Рекурсивное создание вложенных блоков
    def _map_blocks_to_bd(block: TheoryBlock, 
                         parent: Optional[TheoryBlockBD] = None) -> TheoryBlockBD:
        bd_block = TheoryBlockBD(
            content=block.content,
            type=block.type,
            order=block.order,
            parent=parent,
            theory=bd_theory if parent is None else None
        )
        # Рекурсия для children
        bd_block.children = [_map_blocks_to_bd(child, bd_block) 
                            for child in block.children]
        return bd_block

    bd_theory.blocks = [_map_blocks_to_bd(block) for block in theory.blocks]
    await session.commit()
    return bd_theory
```

**2. Eager Loading для избежания N+1:**
```python
async def get_theory_by_id(self, session: AsyncSession, id: int) -> Theory | None:
    stmt = (
        select(TheoryBD)
        .where(TheoryBD.id == id)
        .options(
            selectinload(TheoryBD.blocks)
            .selectinload(TheoryBlockBD.children)
        )
    )
    result = await session.execute(stmt)
    res = result.scalars().one_or_none()

    # Рекурсивная загрузка всех уровней вложенности
    for block in res.blocks:
        if block.children:
            block.children = await self.get_children_by_parent_id(session, block.id)

    return res
```

**3. Сортировка по бизнес-логике:**
```python
async def get_all_task_groups_for_subject(self, session: AsyncSession, 
                                         subject_id: int) -> list[TaskTheoryGroupBD]:
    stmt = (
        select(TaskTheoryGroupBD)
        .where(TaskTheoryGroupBD.subject_id == subject_id)
        .options(
            selectinload(TaskTheoryGroupBD.tasks_theories)
            .selectinload(TaskTheoryBD.theory_associations)
            .selectinload(TaskTheoryAssociation.theory)
        )
    )
    res = await session.execute(stmt)
    groups: list[TaskTheoryGroupBD] = res.scalars().all()

    # Сортировка по номерам в названии
    def sort_task_group(group: TaskTheoryGroupBD):
        group.tasks_theories.sort(
            key=lambda t: int(t.name.replace('-', ' ').split()[0])
        )
        for task in group.tasks_theories:
            task.theory_associations.sort(key=lambda a: a.order)

    for group in groups:
        sort_task_group(group)

    groups.sort(key=lambda g: int(g.name.replace('-', ' ').split()[0]))
    return groups
```

**4. CRUD операции для форм:**
- `create_theory_base()` - создание базы теории
- `update_theory_base()` - обновление метаданных
- `create_block()` - добавление блока
- `update_block()` - изменение блока
- `delete_block()` - удаление с cascade
- `replace_task_theory_links()` - полная замена связей

**5. Association Object с порядком:**
```python
async def replace_task_theory_links(self, session: AsyncSession, 
                                   task_id: int, theory_ids: list[int]) -> None:
    # Удаляем старые связи
    await session.execute(
        delete(TaskTheoryAssociation)
        .where(TaskTheoryAssociation.task_theory_id == task_id)
    )

    # Создаём новые с порядком
    for order_index, theory_id in enumerate(theory_ids):
        assoc = TaskTheoryAssociation(
            task_theory_id=task_id,
            theory_id=theory_id,
            order=order_index
        )
        session.add(assoc)

    await session.flush()
```

### 4. Scripts (`app/scripts/`)

#### `create.py` - Database Initialization
Создание схемы БД при старте приложения.

```python
async def create_all():
    async with async_engine.begin() as conn:
        async_engine.echo = False
        await conn.run_sync(Base.metadata.create_all)
        async_engine.echo = True
```

Вызывается в `main.py` при lifespan события.

#### `parse_theory.py` - Data Migration Script (Устаревший)
**Назначение:** Первоначальная загрузка теории из текстовых файлов.

**Статус:** Устаревший, используется только для ручного добавления теории или восстановления БД.

**Функционал:**
1. Парсинг структурированных текстовых файлов
2. Построение иерархии блоков по отступам
3. Создание теорий и заданий в БД
4. Связывание заданий с теориями

**Формат входных файлов:**

```
8 Производность
    2 Непроизводные
    4 Без, в, до, для, за...
    8 Производные
        2 От существительных
        4 В течение, в продолжение...
%
% 0 2 1
```

- Блоки разделены `%`
- Первый символ - код типа (0-9 → BlockType)
- Отступы (4 пробела) = уровень вложенности
- Последняя строка: типы теории + предмет

**Конфигурация:**
```python
config = {
    "1": BlockType.title,
    "2": BlockType.subtitle,
    "3": BlockType.rule,
    # ...
}

subject2type_config = {
    TheorySubject.rus: [
        TheoryType.speechpart,
        TheoryType.text,
        # ...
    ],
    # ...
}
```

**Важные функции:**
- `find_blocks()` - извлечение блоков из файла
- `parse_blocks()` - рекурсивный парсинг иерархии
- `create_general_theory()` - создание общей теории
- `create_tasks_theory()` - создание заданий с линками

**Использование:**
```bash
# Полная загрузка данных (раскомментировать в main.py)
# await run_everything()

# Или вручную
python -m app.scripts.parse_theory
```

## ⚙️ Конфигурация и Infrastructure

### Database Configuration (`app/core/db.py`)

```python
# Асинхронный engine
async_engine = create_async_engine(
    f"mysql+asyncmy://{settings.user}:{settings.password}@{settings.host}:{settings.port}/{settings.db}",
    echo=True,  # SQL логирование
)

# Session factory
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base для моделей
Base = declarative_base()
```

### Application Startup (`app/main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Проверка подключения к MySQL
    while True:
        try:
            conn = await asyncmy.connect(
                host=settings.host,
                user=settings.user,
                password=settings.password,
                database=settings.db,
                port=int(settings.port)
            )
            await conn.ensure_closed()
            print("MySQL is ready!")
            break
        except Exception as e:
            print("Waiting for MySQL...", str(e))
            break

    # Создание таблиц
    await create_all()

    # Опционально: загрузка начальных данных
    # await run_everything()

    yield

app = FastAPI(lifespan=lifespan, root_path='/api')
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎯 Особенности и Best Practices

### 1. Асинхронность (Async/Await)

**Все I/O операции асинхронны:**
```python
async with async_session_factory() as session:
    result = await session.execute(stmt)
    data = await usecase.execute()
```

**Преимущества:**
- Высокая пропускная способность
- Эффективное использование ресурсов
- Неблокирующие операции с БД

### 2. Транзакционность

**Автоматическое управление транзакциями:**
```python
async with session.begin():
    # Все операции в одной транзакции
    await repo.create_theory_base(...)
    await repo.create_block(...)
    # Автоматический commit или rollback при exception
```

**Принципы:**
- Use Case управляет границами транзакции
- Atomic operations
- Rollback при ошибках

### 3. N+1 Problem Prevention

**Eager Loading через selectinload:**
```python
stmt = (
    select(TaskTheoryGroupBD)
    .options(
        selectinload(TaskTheoryGroupBD.tasks_theories)
        .selectinload(TaskTheoryBD.theory_associations)
        .selectinload(TaskTheoryAssociation.theory)
    )
)
```

**Результат:** Один SQL запрос вместо N+1.

### 4. Рекурсивные структуры

**Иерархия блоков с неограниченной вложенностью:**
```python
# Self-referencing в ORM
parent_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("theory_block.id", ondelete="CASCADE")
)

# Рекурсивная загрузка
async def get_children_by_parent_id(self, session, parent_id):
    children = await session.execute(select(TheoryBlockBD)...)
    for child in children:
        if child.children:
            child.children = await self.get_children_by_parent_id(session, child.id)
    return children
```

### 5. Domain-Driven Design Patterns

**Aggregate Roots:**
- `Theory` - управляет своими `TheoryBlock`
- `TaskTheoryGroup` - управляет своими `TaskTheory`

**Repository Pattern:**
- Абстракция (`ITheoryRepository`)
- Реализация (`TheoryRepositoryImpl`)
- Dependency Inversion

**Entity vs Value Object:**
- `Theory`, `TaskTheory` - Entities (имеют идентификатор)
- `BlockType`, `TheorySubject` - Value Objects (неизменяемые)

**Bounded Context:**
- `theory/` - отдельный контекст для теории
- Возможность расширения на другие контексты

### 6. Автоматическая сортировка

**Сортировка по номерам в названии:**
```python
# "1-3 Мини-текст" → extract 1
# "4-7 Большой текст" → extract 4
groups.sort(key=lambda g: int(g.name.replace('-', ' ').split()[0]))
```

**Сортировка по order в Association:**
```python
task.theory_associations.sort(key=lambda a: a.order)
```

## 🔍 Примеры использования API

### 1. Создание теории с блоками

```bash
# Шаг 1: Создать базу теории
POST /api/theory/
Content-Type: application/json

{
  "name": "Местоимения",
  "subject": "rus",
  "type_ids": [1]  # ID типа "Части речи"
}

# Response: {"id": 15, "name": "Местоимения", "blocks": []}
```

```bash
# Шаг 2: Добавить заголовок
POST /api/theory/15/blocks
Content-Type: application/json

{
  "type": "title",
  "content": "Виды местоимений",
  "parent_id": null,
  "order": 0
}

# Response: {"id": 101}
```

```bash
# Шаг 3: Добавить вложенный подзаголовок
POST /api/theory/15/blocks
Content-Type: application/json

{
  "type": "subtitle",
  "content": "Личные местоимения",
  "parent_id": 101,  # Parent block
  "order": 0
}
```

### 2. Создание группы заданий и связывание с теориями

```bash
# Шаг 1: Создать группу
POST /api/theory/task-groups
Content-Type: application/json

{
  "name": "1-3 Мини-текст",
  "is_single": false,
  "subject_id": 1  # Русский язык
}

# Response: {"id": 5}
```

```bash
# Шаг 2: Добавить задание
POST /api/theory/task-groups/5/tasks
Content-Type: application/json

{
  "name": "1 На месте пропуска..."
}

# Response: {"id": 20}
```

```bash
# Шаг 3: Связать с теориями (с порядком)
PUT /api/theory/tasks/20/theories
Content-Type: application/json

{
  "theory_ids": [15, 7, 3]  # Порядок важен!
}

# Response: {"success": true}
```

### 3. Получение теории со всеми блоками

```bash
GET /api/theory/get_theory/15

# Response:
{
  "id": 15,
  "name": "Местоимения",
  "blocks": [
    {
      "id": 101,
      "type": "title",
      "content": "Виды местоимений",
      "order": 0,
      "parent_id": null,
      "theory_id": 15,
      "children": [
        {
          "id": 102,
          "type": "subtitle",
          "content": "Личные местоимения",
          "order": 0,
          "parent_id": 101,
          "children": []
        }
      ]
    }
  ]
}
```

### 4. Получение заданий по предмету

```bash
GET /api/theory/get_tasks_theory_for_subject/1

# Response:
[
  {
    "task_group_id": 5,
    "group_name": "1-3 Мини-текст",
    "is_single": false,
    "tasks": [
      {
        "task_id": 20,
        "task_name": "1 На месте пропуска...",
        "theories": [
          {
            "theory_id": 15,
            "theory_name": "Местоимения"
          },
          {
            "theory_id": 7,
            "theory_name": "Предлоги"
          }
        ]
      }
    ]
  }
]
```

## 🧪 Тестирование

### Unit Tests (пример)

```python
import pytest
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.enums import BlockType, TheorySubject

def test_theory_entity_creation():
    theory = Theory(
        name="Тест",
        subj=TheorySubject.rus
    )
    assert theory.name == "Тест"
    assert len(theory.blocks) == 0

def test_theory_block_hierarchy():
    parent = TheoryBlock(
        type=BlockType.group,
        content="Группа",
        order=0
    )
    child = TheoryBlock(
        type=BlockType.text,
        content="Текст",
        order=0
    )
    parent.children.append(child)

    assert len(parent.children) == 1
    assert parent.children[0].content == "Текст"
```

### Integration Tests (пример с БД)

```python
@pytest.mark.asyncio
async def test_create_theory_use_case():
    repo = TheoryRepositoryImpl()
    usecase = CreateTheoryBaseUseCase(repo)

    theory = await usecase.execute(
        name="Тестовая теория",
        subject=TheorySubject.rus,
        type_ids=[1]
    )

    assert theory.id is not None
    assert theory.name == "Тестовая теория"
```

## 📦 Развертывание

### Docker Compose (пример)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - DB_USER=pumrus
      - DB_PASSWORD=secret
      - DB_NAME=pumrus
      - DB_PORT=3306
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_DATABASE=pumrus
      - MYSQL_USER=pumrus
      - MYSQL_PASSWORD=secret
      - MYSQL_ROOT_PASSWORD=rootsecret
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

### Production Checklist

- [ ] Настроить конкретные CORS origins
- [ ] Использовать переменные окружения для секретов
- [ ] Настроить логирование (не echo=True в SQLAlchemy)
- [ ] Добавить rate limiting
- [ ] Настроить connection pooling для БД
- [ ] Использовать Dependency Injection для репозиториев
- [ ] Добавить мониторинг и metrics
- [ ] Настроить backup базы данных

## 🤝 Contributing

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Следуйте DDD принципам:
   - Domain не зависит от Infrastructure
   - Use Cases координируют, не содержат логику
   - Repository - только абстракция в Domain
4. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
5. Push в branch (`git push origin feature/AmazingFeature`)
6. Откройте Pull Request

## 📚 Дополнительные ресурсы

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Domain-Driven Design by Eric Evans](https://domainlanguage.com/ddd/)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## 📄 Лицензия

Информация о лицензии отсутствует в репозитории.

## 👥 Автор

- GitHub: [@dakdolka](https://github.com/dakdolka)

## 🔗 Ссылки

- **GitHub Repository:** [https://github.com/dakdolka/pumrus.git](https://github.com/dakdolka/pumrus.git)
- **API Documentation (Swagger):** `http://localhost:8000/api/docs` (после запуска)
- **ReDoc:** `http://localhost:8000/api/redoc`

---

**Архитектура:** Domain-Driven Design (DDD)  
**Версия документации:** 2.0  
**Дата обновления:** 17 февраля 2026
