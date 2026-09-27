from rest_framework.routers import DefaultRouter

from products.views import ProductItemViewSet, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("product-items", ProductItemViewSet, basename="product-item")

urlpatterns = router.urls
