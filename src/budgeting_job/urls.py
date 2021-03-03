from django.urls import path, include
from rest_framework.routers import DefaultRouter

from budgeting.views import ImportPlaidTransactionView, EndBudgetNotifyView

router = DefaultRouter()

patterns = ([
    path('', include(router.urls)),
    path('import-plaid-transaction/', ImportPlaidTransactionView.as_view(), name='import-plaid-transaction-view'),
    path('end-budget-notify/', EndBudgetNotifyView.as_view(), name='end-budget-notify-view'),

    # path('run-pubsub/', SubView.as_view()),

    # path('manual-job/', ManualJobView.as_view(), name='manual-job-view'),
], 'budget-job')

urlpatterns = [
    path('budget-job/', include(patterns)),
]
