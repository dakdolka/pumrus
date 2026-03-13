from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.tasks.parsers import get_parser, ParsedItem
from app.infra.tasks.general.models import OptionSetBD


class ParseRawUseCase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(
        self,
        parser_type: str,
        raw_items: list,
        option_set_id: Optional[int] = None,
    ) -> list[dict]:
        parser = get_parser(parser_type)
        parsed: list[ParsedItem] = parser.parse_many(raw_items)

        option_map: dict[str, int] = {}
        if option_set_id:
            result = await self.session.execute(
                select(OptionSetBD)
                .options(selectinload(OptionSetBD.options))
                .where(OptionSetBD.id == option_set_id)
            )
            option_set = result.scalars().one_or_none()
            if option_set:
                for opt in option_set.options:
                    option_map[opt.content.strip().lower()] = opt.id

        result_list = []
        for item in parsed:
            first_option = item.correct_options[0] if item.correct_options else None
            correct_option_id = (
                option_map.get(first_option.strip().lower())
                if first_option else None
            )
            result_list.append({
                "content_raw":       item.content_raw,
                "content_visible":   item.content_visible,
                "content_correct":   item.content_correct,
                "correct_options":   item.correct_options,
                "correct_option_id": correct_option_id,
            })

        return result_list
