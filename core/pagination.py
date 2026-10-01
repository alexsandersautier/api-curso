from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ApiPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "page": self.page.number,
                "size": self.page.paginator.per_page,
                "total": self.page.paginator.count,
                "totalPages": self.page.paginator.num_pages
                if self.page.paginator.count
                else 0,
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["page", "size", "total", "totalPages", "results"],
            "properties": {
                "page": {
                    "type": "integer",
                    "example": 1,
                },
                "size": {
                    "type": "integer",
                    "example": self.page_size,
                },
                "total": {
                    "type": "integer",
                    "example": 42,
                },
                "totalPages": {
                    "type": "integer",
                    "example": 3,
                },
                "results": schema,
            },
        }

    def get_schema_operation_parameters(self, view):
        parameters = super().get_schema_operation_parameters(view)
        parameters.append(
            {
                "name": self.page_size_query_param,
                "required": False,
                "in": "query",
                "description": (
                    f"Number of results per page (maximum {self.max_page_size})."
                ),
                "schema": {
                    "type": "integer",
                    "default": self.page_size,
                    "minimum": 1,
                    "maximum": self.max_page_size,
                },
            }
        )
        return parameters
