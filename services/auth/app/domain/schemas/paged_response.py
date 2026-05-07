from typing import Generic, List, TypeVar
from domain.schemas.camel_model import CamelModel

T = TypeVar("T")


class PagedResponse(CamelModel, Generic[T]):
    items: List[T]
    has_more: bool
