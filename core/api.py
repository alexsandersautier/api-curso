from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


@extend_schema(
    tags=["System"],
    summary="Check API health",
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})
