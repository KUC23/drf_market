# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListCreate.as_view(), name='product_list_create'), # 게시글 전체목록 조회
    path('<int:product_pk>/', views.ProductDetail.as_view(), name='product_detail'), # 게시글 상세목록
    path('<int:product_pk>/comments/', views.CommentListCreate.as_view(), name='comments'),  # 댓글 조회
    path('<int:product_pk>/comments/<int:comment_pk>/like/', views.CommentLike.as_view(), name='comment_like'), # 좋아요 확인

]