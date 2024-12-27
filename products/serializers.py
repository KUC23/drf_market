# products/serializers.py
from rest_framework import serializers
from .models import Product
from .models import Comment

class ProductListSerializer(serializers.ModelSerializer):
    "게시글 목록 조회 Serializer"

    class Meta:
        model = Product
        fields = ('id', 'author', 'title', 'created_at', 'view_count')  # 조회수 필드 추가
        read_only_fields = ('author', )
        
        
class ProductDetailSerializer(serializers.ModelSerializer):
    "게시글 상세 조회 및 생성 Serializer"
    author = serializers.ReadOnlyField(source='author.email') # author 필드에 작성자의 이메일만 출력
    
    class Meta:
        model = Product
        fields = ('id', 'author', 'title', 'content', 'created_at', 'updated_at', 'view_count')  # 조회수 필드 추가


class CommentSerializer(serializers.ModelSerializer):
    "댓글 조회 및 생성 Serializer"
    author = serializers.ReadOnlyField(source='author.email')
    like_count = serializers.IntegerField(source='like_users.count', read_only=True)

    # SerializerMethodField : 직렬화 과정 중에 커스텀 데이터를 생성하거나, 모델에 없는 데이터를 추가적으로 포함하고 싶을 때 사용하는 특별한 필드
    # 이 필드는 기본적으로 읽기 전용이며, 데이터를 생성하거나 업데이트하지 않습니다.
    # def get_is_liked(self, obj): 로 메소드를 지정해주어야한다.    
    # 즉, 아래의 'is_liked' 변수는 함수 'get_is_liked' 와 연동되어야한다.
    is_liked = serializers.SerializerMethodField() #좋아요 여부
    
    class Meta:
        model = Comment
        fields = ('id', 'product', 'author', 'content', 'created_at', 
                 'updated_at', 'like_users', 'like_count', 'is_liked')
        read_only_fields = ('product',)
        
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_users.filter(pk=request.user.pk).exists()
        return False