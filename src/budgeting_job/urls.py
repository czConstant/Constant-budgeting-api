from django.urls import path, include
from rest_framework.routers import DefaultRouter

from budgeting_job.views import ImportPlaidTransactionView

router = DefaultRouter()

patterns = ([
    path('', include(router.urls)),
    path('import-plaid-transaction/', ImportPlaidTransactionView.as_view()),

    # path('run-pubsub/', SubView.as_view()),

    # path('manual-job/', ManualJobView.as_view(), name='manual-job-view'),
], 'exchange-job')

urlpatterns = [
    path('budgeting-job/', include(patterns)),
]
