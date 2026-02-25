
import base64
from decimal import Decimal

from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Address, Role, User
from organization.models import Company, Store
from orders.models import (
    CartCoupon,
    CartItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    OrderTracking,
    Wishlist,
    WishlistItem,
)
from products.models import (
    Attachment,
    Brand,
    Product,
    ProductCategory,
    ProductDetailType,
    ProductVariant,
    ProductVariantOption,
    Review,
    ReviewHelpfulVote,
)


class Command(BaseCommand):
    help = "Seed approx target entries for all custom project models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--store-slug",
            type=str,
            default=None,
            help="Optional existing store slug to prioritize for product data",
        )
        parser.add_argument(
            "--target",
            type=int,
            default=20,
            help="Approx minimum rows per model",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        target = max(1, int(options.get("target", 20)))
        counters = {key: 0 for key in [
            "companies",
            "stores",
            "roles",
            "users",
            "addresses",
            "categories",
            "brands",
            "products",
            "variants",
            "variant_options",
            "detail_types",
            "attachments",
            "reviews",
            "review_helpful_votes",
            "coupons",
            "coupon_usages",
            "cart_items",
            "cart_coupons",
            "wishlists",
            "wishlist_items",
            "orders",
            "order_items",
            "order_tracking",
        ]}

        _, primary_store = self._ensure_companies_and_stores(
            target=target,
            store_slug=options.get("store_slug"),
            counters=counters,
        )

        self._ensure_roles(target, primary_store, counters)
        users = self._ensure_users(target, primary_store, counters)
        addresses = self._ensure_addresses(target, users, counters)

        self._ensure_categories(target, primary_store, counters)
        self._ensure_category_expansion(primary_store, counters)

        categories = list(
            ProductCategory.objects.filter(store=primary_store, children__isnull=True)
            .distinct()
            .order_by("name")
        )

        self._ensure_brands(target, primary_store, counters)
        self._ensure_curated_catalog(primary_store, counters)

        brands = list(Brand.objects.filter(store=primary_store).order_by("name"))
        self._ensure_products(target, primary_store, categories, brands, counters)
        products = list(Product.objects.filter(store=primary_store).order_by("created_at"))

        variants = self._ensure_variants(target, products, counters)
        self._ensure_variant_options(target, variants, counters)
        self._backfill_recent_product_data(primary_store, products, variants, brands)
        variants = list(ProductVariant.objects.select_related("product").order_by("created_at"))

        self._ensure_detail_types(target, counters)
        reviews = self._ensure_reviews(target, users, products, counters)
        self._ensure_attachments(
            target,
            primary_store,
            categories,
            brands,
            products,
            variants,
            reviews,
            counters,
        )
        self._ensure_review_helpful_votes(target, reviews, users, counters)

        coupons = self._ensure_coupons(target, categories, products, counters)
        self._ensure_coupon_usages(target, coupons, users, counters)
        self._ensure_cart_items(target, users, products, variants, counters)
        self._ensure_cart_coupons(target, coupons, users, counters)
        wishlists = self._ensure_wishlists(target, users, counters)
        self._ensure_wishlist_items(target, wishlists, products, counters)
        orders = self._ensure_orders(target, users, addresses, coupons, variants, counters)
        self._ensure_order_items(target, orders, variants, counters)
        self._ensure_order_tracking(target, orders, counters)

        self.stdout.write(self.style.SUCCESS(f"Demo seed completed (target={target})."))
        for key, value in counters.items():
            self.stdout.write(f"- {key}: +{value}")
        self.stdout.write("Created/updated data for all custom app models.")

    def _ensure_companies_and_stores(self, target, store_slug, counters):
        for i in range(Company.objects.count(), target):
            Company.objects.create(
                name=f"Demo Company {i + 1:02d}",
                description="Demo company for seed data",
                address=f"{100 + i} Market Street, USA",
                is_active=True,
            )
            counters["companies"] += 1

        companies = list(Company.objects.order_by("created_at"))
        requested_store = Store.objects.filter(slug=store_slug).first() if store_slug else None

        for i in range(Store.objects.count(), target):
            company = companies[i % len(companies)]
            Store.objects.create(
                company=company,
                name=f"Store {i + 1:02d}",
                email=f"store{i + 1:02d}@demo.local",
                phone=f"900000{1000 + i}",
                address=f"{200 + i} Commerce Ave",
                is_primary=(i == 0),
                is_active=True,
            )
            counters["stores"] += 1

        stores = list(Store.objects.order_by("created_at"))
        primary_store = requested_store or stores[0]
        return stores, primary_store

    def _ensure_roles(self, target, store, counters):
        for i in range(Role.objects.count(), target):
            Role.objects.create(
                store=store,
                name=f"{store.slug}-role-{i + 1:02d}"[:100],
            )
            counters["roles"] += 1

        roles = list(Role.objects.order_by("name"))
        sample_permissions = list(Permission.objects.filter(codename__startswith="view_")[:5])
        if sample_permissions:
            for role in roles[:target]:
                role.permissions.add(*sample_permissions)

    def _ensure_users(self, target, store, counters):
        existing = User.objects.count()
        for i in range(existing, target):
            User.objects.create_user(
                email=f"demo.user{i + 1:03d}@example.com",
                password="Demo@12345",
                first_name="Demo",
                last_name=f"User{i + 1:03d}",
                number=f"91000{i + 1:05d}",
                store=store,
                is_active=True,
                is_customer=True,
                is_staff=(i % 10 == 0),
            )
            counters["users"] += 1

        return list(User.objects.order_by("date_joined"))

    def _ensure_addresses(self, target, users, counters):
        types = ["home", "work", "other"]
        for i in range(Address.objects.count(), target):
            user = users[i % len(users)]
            Address.objects.create(
                user=user,
                type=types[i % len(types)],
                line1=f"{10 + i} Demo Lane",
                line2="Suite A",
                city="New York",
                state="NY",
                country="USA",
                postal_code=f"10{i:03d}",
                is_primary=(i % len(users) == 0),
            )
            counters["addresses"] += 1
        return list(Address.objects.order_by("created_at"))

    def _get_or_create_category(self, store, name, parent, counters):
        found = ProductCategory.objects.filter(store=store, name=name, parent=parent).first()
        if found:
            return found
        counters["categories"] += 1
        return ProductCategory.objects.create(store=store, name=name, parent=parent)
    def _ensure_categories(self, target, store, counters):
        fashion = self._get_or_create_category(store, "Fashion", None, counters)
        cloth = self._get_or_create_category(store, "Cloth", fashion, counters)

        men = self._get_or_create_category(store, "Men", cloth, counters)
        men_bottomwear = self._get_or_create_category(store, "Bottomwear", men, counters)
        self._get_or_create_category(store, "Jeans", men_bottomwear, counters)
        self._get_or_create_category(store, "Trousers", men_bottomwear, counters)
        self._get_or_create_category(store, "Pants", men_bottomwear, counters)

        women = self._get_or_create_category(store, "Women", cloth, counters)
        women_bottomwear = self._get_or_create_category(store, "Bottomwear", women, counters)
        self._get_or_create_category(store, "Jeans", women_bottomwear, counters)
        self._get_or_create_category(store, "Trousers", women_bottomwear, counters)
        self._get_or_create_category(store, "Pants", women_bottomwear, counters)
        self._get_or_create_category(store, "Skirts", women_bottomwear, counters)

        self._get_or_create_category(store, "Kids", cloth, counters)

        existing_count = ProductCategory.objects.filter(store=store).count()
        for i in range(existing_count, target):
            self._get_or_create_category(store, f"Demo Category {i + 1:02d}", cloth, counters)

        return list(
            ProductCategory.objects.filter(store=store, children__isnull=True).distinct().order_by("name")
        )

    def _ensure_category_expansion(self, store, counters):
        hierarchy = {
            "Fashion": {
                "Cloth": {
                    "Men": {
                        "Topwear": ["T-Shirts", "Shirts"],
                        "Bottomwear": ["Jeans", "Trousers", "Chinos", "Joggers"],
                        "Footwear": ["Sneakers", "Loafers", "Sandals"],
                        "Ethnic": ["Kurtas", "Nehru Jackets"],
                        "Winterwear": ["Jackets", "Sweatshirts"],
                    },
                    "Women": {
                        "Topwear": ["Tops", "Shirts", "Dresses"],
                        "Bottomwear": ["Jeans", "Trousers", "Leggings", "Skirts"],
                        "Ethnic": ["Kurtis", "Sarees", "Dupattas"],
                        "Footwear": ["Heels", "Flats", "Sandals"],
                        "Accessories": ["Handbags", "Belts"],
                    },
                    "Kids": {
                        "Boys": ["T-Shirts", "Shorts", "Jeans"],
                        "Girls": ["Frocks", "Tops", "Leggings"],
                        "Baby": ["Rompers", "Onesies"],
                        "Footwear": ["School Shoes", "Sandals"],
                    },
                }
            },
            "Home": {
                "Kitchen Gadgets": {
                    "Kitchen Appliances": ["Mixer Grinders", "Toasters", "Electric Kettles"],
                },
                "Kitchen Essentials": {
                    "Cookware": ["Frying Pans", "Pressure Cookers", "Saucepans"],
                    "Storage": ["Containers", "Spice Racks", "Lunch Boxes"],
                    "Tableware": ["Plates", "Bowls", "Cutlery"],
                },
                "Home Decoration": {
                    "Wall Decor": ["Wall Art", "Mirrors", "Clocks"],
                    "Lighting": ["Lamps", "Fairy Lights", "Pendant Lights"],
                    "Soft Furnishing": ["Cushion Covers", "Curtains", "Throws"],
                    "Decor Accents": ["Vases", "Candles", "Showpieces"],
                },
            },
        }

        def walk(parent, node):
            if isinstance(node, dict):
                for name, child in node.items():
                    current = self._get_or_create_category(store, name, parent, counters)
                    walk(current, child)
                return
            for leaf_name in node:
                self._get_or_create_category(store, leaf_name, parent, counters)

        walk(None, hierarchy)

    def _get_or_create_brand_by_name(self, store, name, counters):
        brand = Brand.objects.filter(store=store, name=name).first()
        if brand:
            return brand
        counters["brands"] += 1
        return Brand.objects.create(store=store, name=name, slug="")

    def _category_from_path(self, store, path):
        parent = None
        for segment in path:
            parent = ProductCategory.objects.filter(store=store, name=segment, parent=parent).first()
            if parent is None:
                return None
        return parent
    def _ensure_curated_catalog(self, store, counters):
        specs = [
            {
                "name": "Men Classic Oxford Shirt",
                "brand": "Roadster",
                "category_path": ["Fashion", "Cloth", "Men", "Topwear", "Shirts"],
                "description": "Breathable cotton oxford shirt for daily and office wear.",
                "short": "Men cotton oxford shirt",
                "variants": [
                    {"price": "1299.00", "mrp": "1699.00", "qty": 45, "options": {"color": "White", "size": "M", "fit": "Regular"}},
                    {"price": "1299.00", "mrp": "1699.00", "qty": 40, "options": {"color": "Blue", "size": "L", "fit": "Regular"}},
                ],
            },
            {
                "name": "Men Urban Chino Pants",
                "brand": "Levis",
                "category_path": ["Fashion", "Cloth", "Men", "Bottomwear", "Chinos"],
                "description": "Stretchable chinos with smart tapered silhouette.",
                "short": "Men tapered chinos",
                "variants": [
                    {"price": "1499.00", "mrp": "1999.00", "qty": 38, "options": {"color": "Beige", "size": "32", "fit": "Slim"}},
                    {"price": "1499.00", "mrp": "1999.00", "qty": 30, "options": {"color": "Navy", "size": "34", "fit": "Slim"}},
                ],
            },
            {
                "name": "Women Floral Summer Dress",
                "brand": "H&M",
                "category_path": ["Fashion", "Cloth", "Women", "Topwear", "Dresses"],
                "description": "Soft rayon floral dress with a relaxed fit.",
                "short": "Women floral midi dress",
                "variants": [
                    {"price": "1699.00", "mrp": "2299.00", "qty": 42, "options": {"color": "Pink", "size": "S", "fit": "Regular"}},
                    {"price": "1699.00", "mrp": "2299.00", "qty": 35, "options": {"color": "Black", "size": "M", "fit": "Regular"}},
                ],
            },
            {
                "name": "Women Ethnic Kurti Set",
                "brand": "Biba",
                "category_path": ["Fashion", "Cloth", "Women", "Ethnic", "Kurtis"],
                "description": "Printed kurti set for festive and casual occasions.",
                "short": "Women printed kurti set",
                "variants": [
                    {"price": "1899.00", "mrp": "2499.00", "qty": 28, "options": {"color": "Maroon", "size": "M", "fit": "Regular"}},
                    {"price": "1899.00", "mrp": "2499.00", "qty": 24, "options": {"color": "Teal", "size": "L", "fit": "Regular"}},
                ],
            },
            {
                "name": "Kids Cartoon Graphic Tee",
                "brand": "FirstCry",
                "category_path": ["Fashion", "Cloth", "Kids", "Boys", "T-Shirts"],
                "description": "Soft cotton graphic t-shirt for active kids.",
                "short": "Kids graphic t-shirt",
                "variants": [
                    {"price": "599.00", "mrp": "799.00", "qty": 50, "options": {"color": "Yellow", "size": "6Y", "fit": "Regular"}},
                    {"price": "599.00", "mrp": "799.00", "qty": 44, "options": {"color": "Blue", "size": "8Y", "fit": "Regular"}},
                ],
            },
            {
                "name": "Kids Party Frock",
                "brand": "Hopscotch",
                "category_path": ["Fashion", "Cloth", "Kids", "Girls", "Frocks"],
                "description": "Layered party frock with comfortable lining.",
                "short": "Girls party frock",
                "variants": [
                    {"price": "999.00", "mrp": "1399.00", "qty": 33, "options": {"color": "Red", "size": "5Y", "fit": "Regular"}},
                    {"price": "999.00", "mrp": "1399.00", "qty": 29, "options": {"color": "Purple", "size": "7Y", "fit": "Regular"}},
                ],
            },
            {
                "name": "Nonstick Frying Pan 28cm",
                "brand": "Prestige",
                "category_path": ["Home", "Kitchen Essentials", "Cookware", "Frying Pans"],
                "description": "3-layer nonstick frying pan with induction base.",
                "short": "28cm nonstick frying pan",
                "variants": [
                    {"price": "1199.00", "mrp": "1599.00", "qty": 26, "options": {"color": "Black", "size": "28cm", "material": "Aluminium"}},
                    {"price": "1299.00", "mrp": "1699.00", "qty": 20, "options": {"color": "Grey", "size": "30cm", "material": "Aluminium"}},
                ],
            },
            {
                "name": "Stainless Steel Lunch Box Set",
                "brand": "Milton",
                "category_path": ["Home", "Kitchen Essentials", "Storage", "Lunch Boxes"],
                "description": "Leakproof steel lunch boxes suitable for office and school.",
                "short": "Steel lunch box set",
                "variants": [
                    {"price": "899.00", "mrp": "1199.00", "qty": 48, "options": {"color": "Silver", "size": "3 Containers", "capacity": "900ml"}},
                    {"price": "1099.00", "mrp": "1399.00", "qty": 36, "options": {"color": "Silver", "size": "4 Containers", "capacity": "1200ml"}},
                ],
            },
            {
                "name": "Electric Kettle 1.5L",
                "brand": "Philips",
                "category_path": ["Home", "Kitchen Gadgets", "Kitchen Appliances", "Electric Kettles"],
                "description": "Fast boiling electric kettle with auto shut-off.",
                "short": "1.5L electric kettle",
                "variants": [
                    {"price": "1599.00", "mrp": "1999.00", "qty": 22, "options": {"color": "Black", "size": "1.5L", "wattage": "1500W"}},
                    {"price": "1699.00", "mrp": "2199.00", "qty": 18, "options": {"color": "White", "size": "1.7L", "wattage": "1500W"}},
                ],
            },
            {
                "name": "Decorative Wall Mirror",
                "brand": "Home Centre",
                "category_path": ["Home", "Home Decoration", "Wall Decor", "Mirrors"],
                "description": "Minimal round mirror for modern living spaces.",
                "short": "Round wall mirror",
                "variants": [
                    {"price": "1999.00", "mrp": "2699.00", "qty": 16, "options": {"color": "Gold", "size": "24 inch", "material": "Metal"}},
                    {"price": "2399.00", "mrp": "2999.00", "qty": 12, "options": {"color": "Black", "size": "30 inch", "material": "Metal"}},
                ],
            },
            {
                "name": "Boho Cushion Cover Set",
                "brand": "IKEA",
                "category_path": ["Home", "Home Decoration", "Soft Furnishing", "Cushion Covers"],
                "description": "Textured cushion covers to style sofas and beds.",
                "short": "Set of 5 cushion covers",
                "variants": [
                    {"price": "799.00", "mrp": "1099.00", "qty": 34, "options": {"color": "Beige", "size": "16x16", "material": "Cotton"}},
                    {"price": "899.00", "mrp": "1199.00", "qty": 27, "options": {"color": "Multicolor", "size": "18x18", "material": "Cotton"}},
                ],
            },
            {
                "name": "Decor Scented Candle Pack",
                "brand": "Miniso",
                "category_path": ["Home", "Home Decoration", "Decor Accents", "Candles"],
                "description": "Aromatic candle pack for cozy home ambience.",
                "short": "Scented candle pack",
                "variants": [
                    {"price": "499.00", "mrp": "699.00", "qty": 40, "options": {"color": "Ivory", "size": "Pack of 4", "fragrance": "Vanilla"}},
                    {"price": "499.00", "mrp": "699.00", "qty": 38, "options": {"color": "Ivory", "size": "Pack of 4", "fragrance": "Lavender"}},
                ],
            },
        ]

        for spec in specs:
            category = self._category_from_path(store, spec["category_path"])
            if category is None:
                continue

            brand = self._get_or_create_brand_by_name(store, spec["brand"], counters)

            product = Product.objects.filter(store=store, name=spec["name"]).first()
            if product is None:
                product = Product.objects.create(
                    store=store,
                    name=spec["name"],
                    description=spec["description"],
                    short_description=spec["short"],
                    category=category,
                    brand=brand,
                    is_active=True,
                )
                counters["products"] += 1
            else:
                changed = []
                if not product.brand_id:
                    product.brand = brand
                    changed.append("brand")
                if not product.description:
                    product.description = spec["description"]
                    changed.append("description")
                if not product.short_description:
                    product.short_description = spec["short"]
                    changed.append("short_description")
                if changed:
                    product.save(update_fields=changed)

            for variant_spec in spec["variants"]:
                desired_options = variant_spec["options"]
                matched = None
                for variant in product.variants.prefetch_related("options").all():
                    option_map = {o.key: o.value for o in variant.options.all()}
                    if option_map == desired_options:
                        matched = variant
                        break

                if matched is None:
                    matched = ProductVariant.objects.create(
                        product=product,
                        price=Decimal(variant_spec["price"]),
                        mrp=Decimal(variant_spec["mrp"]),
                        quantity=variant_spec["qty"],
                    )
                    counters["variants"] += 1

                for key, value in desired_options.items():
                    _, created = ProductVariantOption.objects.get_or_create(
                        variant=matched,
                        key=key,
                        value=value,
                    )
                    if created:
                        counters["variant_options"] += 1

    def _ensure_brands(self, target, store, counters):
        for i in range(Brand.objects.filter(store=store).count(), target):
            Brand.objects.create(store=store, name=f"Demo Brand {i + 1:02d}", slug="")
            counters["brands"] += 1
        return list(Brand.objects.filter(store=store).order_by("name"))

    def _ensure_products(self, target, store, categories, brands, counters):
        existing = Product.objects.filter(store=store).count()
        for i in range(existing, target):
            Product.objects.create(
                store=store,
                name=f"Demo Product {i + 1:03d}",
                description=f"Long description for demo product {i + 1:03d}.",
                short_description=f"Short description {i + 1:03d}",
                category=categories[i % len(categories)],
                brand=brands[i % len(brands)],
                is_active=True,
            )
            counters["products"] += 1

        return list(Product.objects.filter(store=store).order_by("created_at"))

    def _ensure_variants(self, target, products, counters):
        colors = ["Black", "Blue", "Grey", "Navy", "Olive", "White"]
        sizes = ["S", "M", "L", "XL", "30", "32", "34", "36"]

        for i in range(ProductVariant.objects.count(), target):
            product = products[i % len(products)]
            variant = ProductVariant.objects.create(
                product=product,
                price=Decimal("999.00") + Decimal(i * 10),
                mrp=Decimal("1299.00") + Decimal(i * 10),
                quantity=40 + (i % 15),
            )
            counters["variants"] += 1

            for key, value in {
                "color": colors[i % len(colors)],
                "size": sizes[i % len(sizes)],
            }.items():
                _, created = ProductVariantOption.objects.get_or_create(
                    variant=variant,
                    key=key,
                    value=value,
                )
                if created:
                    counters["variant_options"] += 1

        return list(ProductVariant.objects.select_related("product").order_by("created_at"))
    def _ensure_variant_options(self, target, variants, counters):
        if ProductVariantOption.objects.count() >= target:
            return

        fits = ["Regular", "Slim", "Relaxed"]
        idx = 0
        while ProductVariantOption.objects.count() < target:
            variant = variants[idx % len(variants)]
            _, created = ProductVariantOption.objects.get_or_create(
                variant=variant,
                key="fit",
                value=fits[idx % len(fits)],
            )
            if created:
                counters["variant_options"] += 1
            idx += 1

    def _backfill_recent_product_data(self, store, products, variants, brands):
        default_brand = brands[0] if brands else None

        for idx, product in enumerate(products):
            changed_fields = []
            if not product.brand_id and default_brand:
                product.brand = default_brand
                changed_fields.append("brand")
            if not product.description:
                product.description = f"Long description for demo product {idx + 1:03d}."
                changed_fields.append("description")
            if not product.short_description:
                product.short_description = f"Short description {idx + 1:03d}"
                changed_fields.append("short_description")
            if changed_fields:
                product.save(update_fields=changed_fields)

        color_palette = ["Black", "Blue", "Grey", "Navy", "Olive", "White"]
        size_palette = ["S", "M", "L", "XL", "30", "32", "34", "36"]

        for idx, variant in enumerate(variants):
            changed_fields = []
            if variant.price is None or variant.price <= 0:
                variant.price = Decimal("999.00") + Decimal(idx * 10)
                changed_fields.append("price")
            if variant.mrp is None or variant.mrp <= 0:
                variant.mrp = variant.price + Decimal("300.00")
                changed_fields.append("mrp")
            if changed_fields:
                variant.save(update_fields=changed_fields)

            ProductVariantOption.objects.get_or_create(
                variant=variant,
                key="color",
                defaults={"value": color_palette[idx % len(color_palette)]},
            )
            ProductVariantOption.objects.get_or_create(
                variant=variant,
                key="size",
                defaults={"value": size_palette[idx % len(size_palette)]},
            )

        store_products = [p for p in products if p.store_id == store.id]
        for idx, product in enumerate(store_products):
            if product.variants.exists():
                continue

            variant = ProductVariant.objects.create(
                product=product,
                price=Decimal("999.00") + Decimal(idx * 10),
                mrp=Decimal("1299.00") + Decimal(idx * 10),
                quantity=40,
            )
            ProductVariantOption.objects.get_or_create(
                variant=variant,
                key="color",
                value=color_palette[idx % len(color_palette)],
            )
            ProductVariantOption.objects.get_or_create(
                variant=variant,
                key="size",
                value=size_palette[idx % len(size_palette)],
            )

    def _ensure_detail_types(self, target, counters):
        for i in range(ProductDetailType.objects.count(), target):
            ProductDetailType.objects.create(name=f"Detail Type {i + 1:02d}", is_active=True)
            counters["detail_types"] += 1

    def _ensure_attachments(self, target, store, categories, brands, products, variants, reviews, counters):
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Zx1sAAAAASUVORK5CYII="
        )

        entity_groups = [
            ("category", categories),
            ("brand", brands),
            ("product", products),
            ("variation", variants),
            ("review", reviews),
        ]

        for entity_type, objects in entity_groups:
            for idx, obj in enumerate(objects):
                has_image = Attachment.objects.filter(
                    store=store,
                    entity_type=entity_type,
                    entity_id=obj.id,
                    file_type="image",
                ).exists()
                if has_image:
                    continue

                payload = ContentFile(png_bytes, name=f"seed_{entity_type}_{idx + 1:03d}.png")
                Attachment.objects.create(
                    entity_type=entity_type,
                    entity_id=obj.id,
                    store=store,
                    file=payload,
                    is_primary=True,
                )
                counters["attachments"] += 1

        attachments_in_store = Attachment.objects.filter(store=store).count()
        for i in range(attachments_in_store, target):
            product = products[i % len(products)]
            payload = ContentFile(png_bytes, name=f"seed_extra_{i + 1:03d}.png")
            Attachment.objects.create(
                entity_type="product",
                entity_id=product.id,
                store=store,
                file=payload,
                is_primary=False,
            )
            counters["attachments"] += 1

    def _ensure_reviews(self, target, users, products, counters):
        for i in range(Review.objects.count(), target):
            user = users[i % len(users)]
            product = products[i % len(products)]
            Review.objects.create(
                user=user,
                product=product,
                rating=(i % 5) + 1,
                title=f"Demo Review {i + 1:03d}",
                review_text=f"This is demo review text number {i + 1:03d}.",
            )
            counters["reviews"] += 1

        return list(Review.objects.select_related("user", "product").order_by("created_at"))

    def _ensure_review_helpful_votes(self, target, reviews, users, counters):
        idx = 0
        while ReviewHelpfulVote.objects.count() < target:
            review = reviews[idx % len(reviews)]
            user = users[(idx + 1) % len(users)]
            _, created = ReviewHelpfulVote.objects.get_or_create(review=review, user=user)
            if created:
                counters["review_helpful_votes"] += 1
            idx += 1
    def _ensure_coupons(self, target, categories, products, counters):
        now = timezone.now()
        for i in range(Coupon.objects.count(), target):
            coupon = Coupon.objects.create(
                code=f"DEMO{i + 1:03d}",
                discount_type="percent" if i % 2 == 0 else "flat",
                discount_value=Decimal("10.00") if i % 2 == 0 else Decimal("150.00"),
                max_discount_amount=Decimal("500.00"),
                min_order_amount=Decimal("499.00"),
                scope="cart" if i % 3 == 0 else "category",
                active=True,
                start_date=now,
            )
            coupon.applicable_products.add(products[i % len(products)])
            coupon.applicable_categories.add(categories[i % len(categories)])
            counters["coupons"] += 1

        return list(Coupon.objects.order_by("created_at"))

    def _ensure_coupon_usages(self, target, coupons, users, counters):
        idx = 0
        while CouponUsage.objects.count() < target:
            coupon = coupons[idx % len(coupons)]
            user = users[idx % len(users)]
            _, created = CouponUsage.objects.get_or_create(
                coupon=coupon,
                user=user,
                defaults={"times_used": idx % 4},
            )
            if created:
                counters["coupon_usages"] += 1
            idx += 1

    def _ensure_cart_items(self, target, users, products, variants, counters):
        idx = 0
        while CartItem.objects.count() < target:
            user = users[idx % len(users)]
            variant = variants[idx % len(variants)]
            product = variant.product
            _, created = CartItem.objects.get_or_create(
                user=user,
                product=product,
                variation=variant,
                defaults={"quantity": (idx % 3) + 1},
            )
            if created:
                counters["cart_items"] += 1
            idx += 1

    def _ensure_cart_coupons(self, target, coupons, users, counters):
        max_possible = min(target, len(users))
        for i in range(CartCoupon.objects.count(), max_possible):
            user = users[i]
            coupon = coupons[i % len(coupons)]
            if CartCoupon.objects.filter(user=user).exists():
                continue
            CartCoupon.objects.create(user=user, coupon=coupon)
            counters["cart_coupons"] += 1

    def _ensure_wishlists(self, target, users, counters):
        idx = 0
        while Wishlist.objects.count() < target:
            user = users[idx % len(users)]
            name = f"Wishlist {idx + 1:03d}"
            _, created = Wishlist.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    "is_system": idx % 2 == 0,
                    "is_primary": idx % len(users) == 0,
                },
            )
            if created:
                counters["wishlists"] += 1
            idx += 1
        return list(Wishlist.objects.order_by("created_at"))

    def _ensure_wishlist_items(self, target, wishlists, products, counters):
        idx = 0
        while WishlistItem.objects.count() < target:
            wishlist = wishlists[idx % len(wishlists)]
            product = products[idx % len(products)]
            _, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product,
            )
            if created:
                counters["wishlist_items"] += 1
            idx += 1

    def _ensure_orders(self, target, users, addresses, coupons, variants, counters):
        for i in range(Order.objects.count(), target):
            user = users[i % len(users)]
            address = addresses[i % len(addresses)] if addresses else None
            coupon = coupons[i % len(coupons)]
            variant = variants[i % len(variants)]
            subtotal = variant.price
            discount = Decimal("50.00")
            total = subtotal - discount

            Order.objects.create(
                user=user,
                coupon=coupon,
                subtotal=subtotal,
                discount_amount=discount,
                total_amount=total,
                status="pending",
                shipping_address=address,
            )
            counters["orders"] += 1

        return list(Order.objects.order_by("created_at"))

    def _ensure_order_items(self, target, orders, variants, counters):
        for i in range(OrderItem.objects.count(), target):
            order = orders[i % len(orders)]
            variant = variants[i % len(variants)]
            OrderItem.objects.create(
                order=order,
                product=variant.product,
                variation=variant,
                quantity=(i % 3) + 1,
                price=variant.price,
            )
            counters["order_items"] += 1

    def _ensure_order_tracking(self, target, orders, counters):
        notes = ["Order placed", "Packed", "Awaiting dispatch", "In transit"]
        for i in range(OrderTracking.objects.count(), target):
            order = orders[i % len(orders)]
            OrderTracking.objects.create(
                order=order,
                status="pending",
                note=notes[i % len(notes)],
            )
            counters["order_tracking"] += 1

