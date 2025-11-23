# Архитектура бэкенда
app/
├── api/                     # Внешний слой: FastAPI + Pydantic + роутеры
│   ├── main.py              # Точка входа FastAPI
│   └── theory/
│       ├── router.py        # маршруты /theory
│       ├── crud.py          # вызовы use_cases и репозиториев
│       └── schemas.py       # Pydantic DTO
├── core/                    # Ядро проекта: бизнес-логика, интерфейсы
│   ├── config.py            # Настройки (env, DB URL и т.д.)
│   ├── db.py                # AsyncEngine, session_factory, Base
│   └── theory/
│       ├── entities.py      # Доменные сущности (TheoryBlock, Theory)
│       ├── repository.py    # Интерфейс доступа к данным (ITheoryRepository)
│       └── use_cases.py     # Бизнес-логика (CreateTheoryUseCase  )
├── infra/                   # Реализация инфраструктуры (БД, внешние сервисы)
│   └── theory/
│       ├── models.py        # SQLAlchemy ORM-модели (TheoryBlockDB, TheoryDB)
│       └── repository_impl.py  # Реализация ITheoryRepository через SQLAlchemy
├── scripts/                 # CLI / вспомогательные скрипты
│   └── parse_theory.py      # Парсер .txt → БД
└── __main__.py              # Можно запускать проект через python -m app
.env

# Запросы к бэку
С фронта просто по соотв путям
/api/theory/all_theory - названия всей теории
и т.д. 