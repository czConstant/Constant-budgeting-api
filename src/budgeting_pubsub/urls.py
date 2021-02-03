from django.urls import path, include
from rest_framework.routers import DefaultRouter

from budgeting_pubsub.views import TestTaskView

router = DefaultRouter()

patterns = ([
    path('', include(router.urls)),
    path('task/test/<int:message_id>/', TestTaskView.as_view()),
], 'exchange-sub')

urlpatterns = [
    path('exchange-sub/', include(patterns)),
]
