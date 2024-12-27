# products/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from .models import Product, Comment
from .serializers import ProductListSerializer, ProductDetailSerializer, CommentSerializer

# setting.py 에서 세팅해주어야 캐시기능 사용가능
from django.core.cache import cache
from .models import Comment

# 클래스 기반의 view함수가 관리하기가 좋다

class ProductListCreate(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        "게시글 목록 조회"
        products = Product.objects.all()
        serializer = ProductListSerializer(products, many=True)  # 목록용 Serializer 사용
        return Response(serializer.data)

    def post(self, request):
        "게시글 생성"
        serializer = ProductDetailSerializer(data=request.data)  # 상세 Serializer 사용
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 

# 클래스는 특정 상품에 대한 조회, 수정, 삭제를 처리
class ProductDetail(APIView):

    # 특정 상품 객체를 조회
    def get_object(self, product_pk):
        return get_object_or_404(Product, pk=product_pk)

    # 특정 상품을 조회
    def get(self, request, product_pk):
        """게시글 상세 조회"""
        product = self.get_object(product_pk)
        # 아래쪽의 함수에서 한번에 해결해도되는데 
        # 굳이 나눈이유는 
        # 유연성과 확장성을 고려했기 때문이다.
        # 유효성 검증 로직 등을 추가 가능     

        # 로그인한 사용자이고 작성자가 아닌 경우에만 조회수 증가 처리
        # 24시간 동안 같은 IP에서 같은 게시글 조회 시 조회수가 증가하지 않음
        if request.user != product.author:        # 작성자가 아닌 경우에만
            # 해당 사용자의 IP와 게시글 ID로 캐시 키를 생성
            cache_key = f"view_count_{request.META.get('REMOTE_ADDR')}_{product_pk}"
            
            # 캐시에 없는 경우에만 조회수 증가
            if not cache.get(cache_key):
                product.view_count += 1
                product.save()
                # 캐시 저장 (10초 유효효)
                cache.set(cache_key, True, 10)

        serializer = ProductDetailSerializer(product)  # 상세 Serializer 사용
        return Response(serializer.data)


    # 상품의 모든 필드를 수정
    def put(self, request, product_pk):
        product = self.get_object(product_pk)
        if request.user != product.author:  # 작성자 확인
            return Response({"error": "수정 권한이 없습니다."}, 
                            status=status.HTTP_403_FORBIDDEN)

        serializer = ProductDetailSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, 
                        status=status.HTTP_400_BAD_REQUEST)


    # 상품의 일부 필드를 수정
    def patch(self, request, product_pk):
        product = self.get_object(product_pk)

        if request.user != product.author: # 작성자 확인
            return Response({"error": "수정 권한이 없습니다."}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # partial=True 옵션을 사용하여, 제공된 데이터만 수정
        serializer = ProductDetailSerializer(product, data=request.data, partial=True)  # 부분 수정
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, 
                        status=status.HTTP_400_BAD_REQUEST)

    # 특정 상품을 삭제
    def delete(self, request, product_pk):
        product = self.get_object(product_pk)
        if request.user != product.author: # 작성자 확인
            return Response({"error": "삭제 권한이 없습니다."}, 
                            status=status.HTTP_403_FORBIDDEN)

        product.delete()
        return Response({"message": "상품이 삭제되었습니다."}, 
                        status=status.HTTP_204_NO_CONTENT)













# 댓글 조회 view
class CommentListCreate(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_product(self, product_pk):
        return get_object_or_404(Product, pk=product_pk)
    
    # GET 요청: 특정 게시글에 달린 댓글 목록 조회
    def get(self, request, product_pk):
        "댓글 목록 조회"
        product = self.get_product(product_pk)
        comments = product.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


    # POST 요청: 특정 게시글에 댓글 생성
    def post(self, request, product_pk):
        "댓글 생성"
        product = self.get_product(product_pk)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, product=product)
            return Response(serializer.data, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, 
                      status=status.HTTP_400_BAD_REQUEST)
        
# 이 클래스는 특정 댓글에 대한 좋아요 기능을 담당하며, 
# 좋아요 상태를 토글합니다(좋아요 추가 및 취소).
class CommentLike(APIView):
    # 특정 게시글을 조회하고 존재하지 않으면 404 응답을 반환
    def get_product(self, product_pk):
        return get_object_or_404(Product, pk=product_pk)

    # 특정 게시글에 속한 댓글을 조회
    # 존재하지 않을 경우 404 응답을 반환
    def get_comment(self, product, comment_pk):
        return get_object_or_404(Comment, pk=comment_pk, product=product)

    # HTTP POST 요청을 처리하며, 특정 댓글에 좋아요 상태를 토글
    #

    def post(self, request, product_pk, comment_pk):
        "댓글 좋아요 토글"
        product = self.get_product(product_pk)          # 게시글 조회
        comment = self.get_comment(product, comment_pk) # 댓글 조회
        user = request.user                             # 요청을 보낸 사용자를 확인 
        
        # 이미 좋아요를 눌렀는지 확인
        if comment.like_users.filter(pk=user.pk).exists():
            # 좋아요 취소
            comment.like_users.remove(user)
            message = "댓글 좋아요가 취소되었습니다."
        else:
            # 좋아요 추가
            comment.like_users.add(user)
            message = "댓글을 좋아요 했습니다."

        # 댓글 정보를 시리얼라이저를 통해 반환
        serializer = CommentSerializer(comment, context={'request': request})
         
        return Response({
            'message': message,
            'comment': serializer.data
        }, status=status.HTTP_200_OK)