from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import(
    RegisterAPI,
    RoleCRUDAPI,
    RoleUpdateDeleteAPI,
    UserListAPI,
    CustomTokenObtainPairView,
    AddressListCreateAPI,
    AddressRetrieveUpdateDeleteAPI
    # ForgotPasswordAPI, 
    # ResetPasswordAPI,
)

urlpatterns = [
    path("register/", RegisterAPI.as_view()),
    path("login/", CustomTokenObtainPairView.as_view()),  
    path("token/refresh/", TokenRefreshView.as_view()),
    # path("forgot-password/", ForgotPasswordAPI.as_view()),
    # path("reset-password/", ResetPasswordAPI.as_view()),

    path("roles/", RoleCRUDAPI.as_view()),
    path("roles/<uuid:pk>/", RoleUpdateDeleteAPI.as_view()),

    path("users/", UserListAPI.as_view()),
    
    path("addresses/", AddressListCreateAPI.as_view()),
    path("addresses/<uuid:pk>/", AddressRetrieveUpdateDeleteAPI.as_view()),
]
