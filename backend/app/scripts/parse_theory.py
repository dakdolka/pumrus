from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(BASE_DIR)
from app.models import BlockType, Theory, TheoryType, Block
from app.core.db import async_session_factory
from sqlalchemy import insert
import asyncio

# python app/scripts/parse_theory.py


config = {
    "1": BlockType.title,
    "2": BlockType.subtitle,
    "3": BlockType.rule,
    "4": BlockType.example,
    "5": BlockType.exception,
    "6": BlockType.important,
    "7": BlockType.text
}

type_config = {
    "0": TheoryType.speechpart,
    "1": TheoryType.text,
    "2": TheoryType.wordparts,
    "3": TheoryType.punctuation
}

async def insert_theory():
    async with async_session_factory() as session:
        theory_type = input("Введите тип теории: ")
        content = input("Введите название теории: ")
        stmt = insert(Theory).values(type=type_config[theory_type], name=content).returning(Theory.id)
        result = await session.execute(stmt)
        new_id = result.scalar_one()
        await session.commit()
        return new_id
        
async def insert_block(type, content, theory_id):
        async with async_session_factory() as session:
            stmt = insert(Block).values(type=type, text=content, theory_id=theory_id).returning(Block.id)
            result = await session.execute(stmt)
            new_id = result.scalar_one()
            await session.commit()
            return new_id
        

async def script():
    file_path = BASE_DIR / 'app' / 'txts' / input("Введите имя файла: ")
    with open(file_path, encoding='utf-8') as f:
        text = f.read()
    text = text.split('*')
    theory_id = await insert_theory()
    for elem in text:
        elem_type = config[elem[0]]
        try:
            elem_content = elem[4:len(elem)-2]
        except Exception as e:
            print(e)
            continue
        await insert_block(elem_type, elem_content, theory_id)

if __name__ == "__main__":
    asyncio.run(script())
    
    
    

