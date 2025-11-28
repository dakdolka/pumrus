from pathlib import Path
from pprint import pprint
import sys
from typing import Optional
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from app.infra.theory.models import TheoryBD, TheoryBlockBD
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.enums import BlockType, TheoryType, TheorySubject
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import CreateTheoryTypesAndSubjsUseCase, CreateTheoryUseCase
import asyncio
import os


# python -m app.scripts.parse_theory


config = {
    "0": None,
    "1": BlockType.title,
    "2": BlockType.subtitle,
    "3": BlockType.rule,
    "4": BlockType.example, 
    "5": BlockType.exception,
    "6": BlockType.important,
    "7": BlockType.text,
    "8": BlockType.group
}

subject_config = {
    "0": TheorySubject.rus,
    "1": TheorySubject.infa
}

type_config = {
    "0": TheoryType.speechpart,
    "1": TheoryType.text,
    "2": TheoryType.wordparts,
    "3": TheoryType.punctuation,
    "4": TheoryType.database,
    "5": TheoryType.encoding
}

subject2type_config = {
    TheorySubject.rus: [
        TheoryType.speechpart, 
        TheoryType.text, 
        TheoryType.wordparts, 
        TheoryType.punctuation
        ],
    TheorySubject.infa: [
        TheoryType.database, 
        TheoryType.encoding
        ]
}


async def find_blocks(dirpath, filename) -> tuple[str, str, list[str]]:
    full_path = os.path.join(dirpath, filename)
    with open(full_path, encoding='utf-8') as f:
        text = f.read()
    text = [elem.strip() for elem in text.split('%')]
    last = text.pop(-1).strip().split()
    theory_types = [type_config[elem] for elem in last[1:len(last)-1]]
    theory_subj = subject_config[last[-1]]
    theory_blocks = [elem.strip() for elem in text]
    return theory_types, theory_subj, theory_blocks

def split_multiline_block(block: str) -> list[tuple[int, str]]:
    result = []
    for raw_line in block.split("\n"):
        if raw_line.strip() == "":
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" ")) #Отступ
        line = raw_line.strip()
        result.append((indent, line))
    return result

async def parse_blocks(raw_blocks: list[str]):
    # 1) Собираем все строки в один список уровня indent
    lines = []

    for block in raw_blocks:
        if block.strip() == "":
            continue
        lines.extend(split_multiline_block(block))

    # Теперь lines выглядит так. Сделано чтобы делить по отступам а не по \n. 
    # Чтобы не слетала вторая вложенность
    # [(0, '8 Производность'),
    #  (4, '2 Непроизводные'),
    #  (4, '4 Без, ...'),
    #  (4, '8 Производные'),
    #  (8, '2 От существительных'),
    #  (8, '4 В течение...'),
    #   ... ]

    idx = 0
    
    async def parse_level(expected_indent: int):
        nonlocal idx # Внешняя но содержащаяся в ф-ции переменная
        items = []

        while idx < len(lines):
            indent, text = lines[idx]
            if indent != expected_indent:
                break

            block_type = config[text[0]]
            content = text[1:].strip()
            idx += 1

            # Если это группа → рекурсивно собираем детей
            if block_type == BlockType.group:
                children = await parse_level(expected_indent + 4) 
                items.append(TheoryBlock(
                    type=block_type, content=content, order=len(items), children=children
                ))
            else:
                items.append(TheoryBlock(
                    type=block_type, content=content, order=len(items), children=[]
                ))

        return items

    blocks = await parse_level(0)
    title = blocks[0].content if blocks else None
    return title, blocks

async def create_theory_types_and_subjs():
    repository = TheoryRepositoryImpl()
    usecase = CreateTheoryTypesAndSubjsUseCase(repository)
    await usecase.execute(subject2type_config)

async def create_theory():
    await create_theory_types_and_subjs()
    repository = TheoryRepositoryImpl()
    usecase = CreateTheoryUseCase(repository)
    dir_path = BASE_DIR / 'app' / 'scripts' / 'txts'
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for filename in filenames:
            theory_types, theory_subj, theory_blocks = await find_blocks(dirpath, filename)
            theory_name, theory_blocks = await parse_blocks(theory_blocks)
            theory = Theory(
                types=theory_types,
                subj=theory_subj,
                name=theory_name,
                blocks=theory_blocks
            )
            # pprint(theory)
            await usecase.execute(theory)
    return 'Success!'


if __name__ == "__main__":
    asyncio.run(create_theory())
    
    
    

