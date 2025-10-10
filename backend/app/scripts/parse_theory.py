from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from app.core.theory.entities import Theory, TheoryBlock
from app.core.theory.enums import BlockType, TheoryType
from app.core.theory.repository import ITheoryRepository
from app.core.theory.use_cases import CreateTheoryUseCase
import asyncio


# python app/scripts/parse_theory.py


config = {
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
    repository = ITheoryRepository()
    usecase = CreateTheoryUseCase(repository)
    
    file_path = BASE_DIR / 'app' / 'scripts' / 'txts' / input("Введите имя файла: ")
    with open(file_path, encoding='utf-8') as f:
        text = f.read()
    text = text.split('#')
    print(text)
    theory = Theory(
        id = None,
        type = type_config[input("Введите тип теории: ")],
        name = input("Введите название теории: "),
        blocks = []
    )
    for elem in text:
        if not elem:
            continue
        elem_type = config[elem[0]]
        elem_content = elem[1:].strip()
        theory.blocks.append(TheoryBlock(id=None, type=elem_type, content=elem_content, theory_id=theory.id))
    saved_theory = await usecase.execute(theory)
    return saved_theory


if __name__ == "__main__":
    asyncio.run(script())
    
    
    

