from django.db import migrations


def seed_demo_categories(apps, schema_editor):
    Store = apps.get_model("organization", "Store")

    # Use live model so MPTT save logic populates level/lft/rght/tree_id.
    from products.models import ProductCategory

    def get_or_create_category(store_id, name, parent=None):
        category = ProductCategory.objects.filter(
            store_id=store_id,
            name=name,
            parent=parent,
        ).first()
        if category:
            return category
        return ProductCategory.objects.create(
            store_id=store_id,
            name=name,
            parent=parent,
        )

    for store_id in Store.objects.values_list("id", flat=True):
        fashion = get_or_create_category(store_id, "Fashion")
        cloth = get_or_create_category(store_id, "Cloth", parent=fashion)

        men = get_or_create_category(store_id, "Men", parent=cloth)
        men_bottomwear = get_or_create_category(store_id, "Bottomwear", parent=men)
        get_or_create_category(store_id, "Jeans", parent=men_bottomwear)
        get_or_create_category(store_id, "Trousers", parent=men_bottomwear)
        get_or_create_category(store_id, "Pants", parent=men_bottomwear)

        women = get_or_create_category(store_id, "Women", parent=cloth)
        women_bottomwear = get_or_create_category(store_id, "Bottomwear", parent=women)
        get_or_create_category(store_id, "Jeans", parent=women_bottomwear)
        get_or_create_category(store_id, "Trousers", parent=women_bottomwear)
        get_or_create_category(store_id, "Pants", parent=women_bottomwear)
        get_or_create_category(store_id, "Skirts", parent=women_bottomwear)

        get_or_create_category(store_id, "Kids", parent=cloth)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0002_company_description_company_slug_store_address_and_more"),
        ("products", "0014_productcategory_level_productcategory_lft_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_demo_categories, reverse_noop),
    ]
