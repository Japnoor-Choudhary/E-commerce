from django.urls import path
from .views import *

urlpatterns = [
    # =========================
    # Cart
    # =========================
    path("cart/", CartListCreateAPI.as_view(), name="cart-list-create"),
    path("cart/<uuid:pk>/", CartDeleteAPI.as_view(), name="cart-delete"),

    # =========================
    # Wishlists
    # =========================
    path("wishlists/", WishlistAPI.as_view(), name="wishlist-list-create"),
    path("wishlists/<uuid:pk>/", WishlistDeleteAPI.as_view(), name="wishlist-delete"),
    path("wishlists/<uuid:wishlist_id>/items/",WishlistItemByFolderAPI.as_view(),name="wishlist-items-by-folder"),

    # =========================
    # Wishlist Items
    # =========================
    path("wishlist-items/",WishlistItemAPI.as_view(),name="wishlist-item-add-list"),
    path("wishlist-items/<uuid:pk>/",WishlistItemDeleteAPI.as_view(),name="wishlist-item-delete"),
    path("wishlist-products/",WishlistProductGroupedAPI.as_view(),name="wishlist-products-grouped"),
    # =========================
    # Orders
    # =========================
    path("order-place/", PlaceOrderAPI.as_view(), name="place-order"),
    
    # =========================
    # Re - Order
    # =========================
    path("re-order/<uuid:order_id>/", ReOrderAPI.as_view(), name="reorder"),
]
