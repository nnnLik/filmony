from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr

from utils.case_converter import to_snake_case

from .mixins import CreatedAtMixin, IntPkMixin


class Base(AsyncAttrs, DeclarativeBase, CreatedAtMixin, IntPkMixin):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f'{to_snake_case(cls.__name__)}'
