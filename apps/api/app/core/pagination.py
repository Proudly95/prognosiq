from fastapi import Query


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
    ):
        self.offset = (page - 1) * size
        self.limit = size
        self.page = page
        self.size = size
