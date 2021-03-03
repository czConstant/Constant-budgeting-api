from model_utils import Choices

NOTIFICATION_TYPE = Choices(
    ('transaction_imported', 'Transaction imported'),
    ('budget_end', 'Budget end'),
    ('budget_over', 'Budget over'),
)

DIRECTION = Choices(
    ('income', 'Income'),
    ('expense', 'Expense')
)

TASK_NOTE = Choices(
    ('first_import_transaction_notification', 'First import transaction notification'),
    ('over_budget_notification', 'over_budget_notification')
)
