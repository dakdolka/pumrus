from pathlib import Path
import pprint
import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.enums import BlockType, TheoryType
from app.infra.theory.repository_impl import TheoryRepositoryImpl
from app.core.theory.use_cases import CreateTheoryUseCase
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
    "8": BlockType.svg
}

type_config = {
    "0": TheoryType.speechpart,
    "1": TheoryType.text,
    "2": TheoryType.wordparts,
    "3": TheoryType.punctuation
}
        

async def script():
    repository = TheoryRepositoryImpl()
    usecase = CreateTheoryUseCase(repository)
    dir_path = BASE_DIR / 'app' / 'scripts' / 'txts'
    for file_name in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, encoding='utf-8') as f:
            text = f.read()
        text = text.split('%')
        theory_type = type_config[text.pop(-1).strip()[-1]]
        theory_blocks: list[TheoryBlock] = []
        for elem in text:
            if not elem:
                continue
            elem_type = config[elem[0]]
            elem_content = elem[1:].strip()
            theory_blocks.append(TheoryBlock(id=None, type=elem_type, content=elem_content, theory_id=None))
        theory_name = theory_blocks[0].content
        print(theory_name, theory_type)
        theory = Theory(
            id = None,
            type = theory_type,
            name = theory_name,
            blocks = theory_blocks
        )
        saved_theory = await usecase.execute(theory)
    return 'Success!'


if __name__ == "__main__":
    asyncio.run(script())
    
    
    

