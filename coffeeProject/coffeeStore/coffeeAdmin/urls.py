from django.urls import path, include
from .views import detailView, loginView, joinView, listView, createView, join, login, createProduct, products, updateProduct, deleteProduct, logout
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("product/create/", createView),
    path("product-create", createProduct),
    path("product-update/<str:product_id>", updateProduct),
    path("product-delete/<str:product_id>", deleteProduct),
    path("products/", products),
    path("product/detail/<str:product_id>/", detailView),
    path("login/", loginView),
    path("join/", joinView),
    path("list/", listView),
    path("user-join", join),
    path("user-login", login),
    path("user-logout", logout),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]

