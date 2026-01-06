from pathlib import Path
from pprint import pprint
import sys
from typing import Optional
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from app.infra.theory.models import TheoryBD, TheoryBlockBD
from app.core.theory.entities import TaskTheory, TaskTheoryGroup, Theory, TheoryBlock
from app.core.theory.enums import BlockType, TheoryType, TheorySubject
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import CreateTasksTheoryUseCase, CreateTheoryTypesAndSubjsUseCase, CreateTheoryUseCase, GetTheoriesByNamesUseCase
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


#TODO возможно стоит enum отдельный ввести
async def find_tasks_theory_blocks(dirpath, filename) -> tuple[list[str], str]:
    full_path = os.path.join(dirpath, filename)
    with open(full_path, encoding='utf-8') as f:
        text = f.read()
    match text.find('%'):
        case 0:
            text = [elem.strip() for elem in text.split('%')]
            theory_blocks = [elem.strip() for elem in text]
            return theory_blocks, 'self theory'
        case -1:
            return [elem.strip() for elem in text.split(',')], 'links'
    

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

async def create_general_theory(dir):
    await create_theory_types_and_subjs()
    repository = TheoryRepositoryImpl()
    usecase = CreateTheoryUseCase(repository)
    dir_path = dir
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
            await usecase.execute(theory)
                
    return 'Success!'

async def create_tasks_theory(dir, subj):
    repository = TheoryRepositoryImpl()
    find_throries_by_name_usecase = GetTheoriesByNamesUseCase(repository)
    theory_insert_usecase = CreateTheoryUseCase(repository)
    task_theory_insert_usecase = CreateTasksTheoryUseCase(repository)
    base_dir_path, subj, task_group, group_name = dir, subject_config[subj], None, None
    for dirpath, dirnames, filenames in os.walk(base_dir_path):
        if filenames == []:
            continue
        parent_thing = [elem for elem in str(dirpath)[len(str(base_dir_path))::].split('/') if elem != '']
        if group_name != parent_thing[0]:
            if task_group:
                await task_theory_insert_usecase.execute(task_group)
            group_name = parent_thing[0]
            task_group = TaskTheoryGroup(
                group_name=group_name,
                is_single = True if len(parent_thing) == 1 else False,
                tasks_theories = []
            )
        task_theory = TaskTheory(
            task_name=parent_thing[1] if len(parent_thing) == 2 else parent_thing[0],
            theories=[]
        )   
        for filename in filenames:
            theory_blocks, ans_type = await find_tasks_theory_blocks(dirpath, filename)
            match ans_type:
                case 'self theory':
                    theory_name, theory_blocks = await parse_blocks(theory_blocks)
                    theory = Theory(
                        subj=subj,
                        name=theory_name,
                        blocks=theory_blocks
                    )
                    first_task_th = await theory_insert_usecase.execute(theory)
                    task_theory.theories.append(first_task_th)
                case 'links':
                    theories = await find_throries_by_name_usecase.execute(theory_blocks)
                    task_theory.theories += theories
        task_group.tasks_theories.append(task_theory)
                    
    

async def run_everything():
    await create_general_theory(BASE_DIR / 'app' / 'scripts' / 'txts' / 'general_theory')
    await create_tasks_theory(BASE_DIR / 'app' / 'scripts' / 'txts' / '.tasks_theory' / 'rus', '0')
    await create_tasks_theory(BASE_DIR / 'app' / 'scripts' / 'txts' / '.tasks_theory' / 'infa', '1')

if __name__ == "__main__":
    asyncio.run(create_general_theory())
    asyncio.run(create_tasks_theory())

