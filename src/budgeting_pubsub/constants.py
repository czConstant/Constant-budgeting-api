from model_utils import Choices

TASK = Choices(
    ('test', 'Test'),
)

RECEIVED_TASK = Choices(
    ('test', 'Test'),
)

SUB_LOG_STATUS = Choices(
    ('success', 'Success'),
    ('failed', 'Failed'),
    ('pending', 'Pending'),
)
