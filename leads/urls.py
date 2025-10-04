from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfferViewSet, LeadViewSet

router = DefaultRouter()
router.register(r'offer', OfferViewSet)
router.register(r'leads', LeadViewSet)  # Changed from 'lead' to 'leads' to match test URLs

urlpatterns = [
    path('', include(router.urls)),
]
