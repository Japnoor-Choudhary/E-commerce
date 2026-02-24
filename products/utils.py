from .models import( 
    ProductCategory,
    CategoryPath
)
from django.db import transaction
def get_descendant_category_ids(category):
    """
    Myntra-style category resolution:
    - If category is a group (Men/Women), include all leaf categories
    - If category is a leaf, include itself
    - Infinite depth supported
    """

    ids = []

    def collect(cat):
        children = ProductCategory.objects.filter(parent=cat)
        if children.exists():
            for child in children:
                collect(child)
        else:
            # leaf category (actual product-holding category)
            ids.append(cat.id)

    collect(category)
    return ids


def get_or_create_category_hierarchy(store, path_string):
    parts = [p.strip().title() for p in path_string.split("/") if p.strip()]
    parent = None
    created_categories = []

    for part in parts:
        category, _ = ProductCategory.objects.get_or_create(
            name=part,
            store=store,
            parent=parent
        )
        created_categories.append(category)
        parent = category

    return created_categories

def save_category_path(store, path_string):
    with transaction.atomic():

        categories = get_or_create_category_hierarchy(store, path_string)

        leaf = categories[-1]
        full_path = " > ".join([c.name for c in categories])

        obj, created = CategoryPath.objects.get_or_create(
            store=store,
            leaf_category=leaf,
            full_path=full_path,
            defaults={"search_count": 1}
        )

        if not created:
            obj.search_count += 1
            obj.save()

        return obj