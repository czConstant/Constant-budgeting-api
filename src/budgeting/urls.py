from django.urls import path, include
from rest_framework.routers import DefaultRouter

from budgeting.resource import CategoryViewSet, TransactionViewSet, WalletViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('wallets', WalletViewSet)
router.register('transactions', TransactionViewSet)

patterns = ([
    path('', include(router.urls)),
], 'budget')

urlpatterns = [
    path('budget/', include(patterns)),
]
