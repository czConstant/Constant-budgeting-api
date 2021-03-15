from django.urls import path, include
from rest_framework.routers import DefaultRouter

from budgeting.resource import CategoryViewSet, TransactionViewSet, WalletViewSet, CategoryGroupViewSet, \
    TransactionNoPagingViewSet, BudgetViewSet, TravelPlanViewSet

router = DefaultRouter()
router.register('category-groups', CategoryGroupViewSet)
router.register('categories', CategoryViewSet)
router.register('wallets', WalletViewSet)
router.register('transactions', TransactionViewSet)
router.register('all-transactions', TransactionNoPagingViewSet, basename='no-paging-transaction')
router.register('budgets', BudgetViewSet)
router.register('travel-plans', TravelPlanViewSet)

patterns = ([
    path('', include(router.urls)),
], 'budget')

urlpatterns = [
    path('budget/', include(patterns)),
]
