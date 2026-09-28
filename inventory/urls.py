from rest_framework.routers import DefaultRouter

from inventory.views import InventoryViewSet

router = DefaultRouter()
router.register("inventory", InventoryViewSet, basename="inventory")

urlpatterns = router.urls
