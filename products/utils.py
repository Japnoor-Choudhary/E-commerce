from .models import ProductCategory

def get_descendant_category_ids(category):
    """
    Recursively returns:
    - category
    - all subcategories
    - all nested subcategories (infinite depth)
    """
    ids = [category.id]

    children = ProductCategory.objects.filter(parent=category)
    for child in children:
        ids.extend(get_descendant_category_ids(child))

    return ids
