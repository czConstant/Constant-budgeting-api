from budgeting.constants import DIRECTION
from budgeting.models import CategoryMapping, Category


class CategoryBusiness:
    category_default = None

    @staticmethod
    def load_category_mapping():
        CategoryBusiness.lazy_load_default_category()

        default_category = Category.DEFAULT_CODE
        category_mapping = {
            DIRECTION.income: {
                default_category: CategoryBusiness.category_default[DIRECTION.income]
            },
            DIRECTION.expense: {
                default_category: CategoryBusiness.category_default[DIRECTION.expense]
            }
        }

        cat_mappings = CategoryMapping.objects.filter(category__deleted_at__isnull=True)
        for cat_mapping in cat_mappings:
            cat = cat_mapping.category
            category_mapping[cat.direction][cat_mapping.name] = cat

        return category_mapping

    @staticmethod
    def default_category(direction):
        CategoryBusiness.lazy_load_default_category()

        return CategoryBusiness.category_default[direction]

    @staticmethod
    def lazy_load_default_category():
        if not CategoryBusiness.category_default:
            CategoryBusiness.category_default = {
                DIRECTION.income: Category.objects.filter(code=Category.DEFAULT_CODE, direction=DIRECTION.income).first(),
                DIRECTION.expense: Category.objects.filter(code=Category.DEFAULT_CODE, direction=DIRECTION.expense).first()
            }
