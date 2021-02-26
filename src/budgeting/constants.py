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
