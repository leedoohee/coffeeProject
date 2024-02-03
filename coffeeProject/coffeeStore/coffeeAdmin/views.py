from rest_framework.decorators import api_view
from django.shortcuts import render
from .models import UserProcessor, User, Product, ProductProcessor, SearchProcessor
from rest_framework.response import Response
import json

@api_view(['GET'])
def createView(request):
    searchProcessor = SearchProcessor()
    addInfo = searchProcessor.searchAddInfo()
    context = {'addInfo': addInfo}
    return render(request, 'create.html', context)

@api_view(['GET'])
def detailView(request, product_id):
    product = Product('', product_id, '', '', '')
    productInfo = product.getInfo()
    searchProcessor = SearchProcessor()
    addInfo = searchProcessor.searchAddInfo()
    context = {'addInfo': addInfo, 'productInfo': productInfo}
    return render(request, 'detail.html', context)

@api_view(['GET'])
def loginView(request):
    return render(request, 'login.html')

@api_view(['GET'])
def joinView(request):
    return render(request, 'join.html')

@api_view(['GET'])
def listView(request):
    return render(request, 'list.html')

@api_view(['GET'])
def products(request):
    searchProcessor = SearchProcessor()

    products = searchProcessor.searchProducts(request)
    return Response(
        {
            "code": 200,
            "data": products
        }
    )

@api_view(['POST'])
def join(request):
    userProcessor = UserProcessor()
    PASSWORD_LENGTH = 8

    try:
        req = json.loads(request.body)

        phone = req['phone']
        password = req['password']

        if password == '' or phone == '':
            return Response({"code": 400, 'message': "이메일 혹은 패스워드가 비어있습니다."}, status=200)

        if len(password) < PASSWORD_LENGTH:
            return Response({"code": 400, "message": "비밀번호는 최소 8자 이상입니다."}, status=200)

        user = User(phone, password)

        if user.exists() == True:
            return Response({"code": 400, "message": "이미 가입한 회원입니다."}, status=200)

        user = userProcessor.createUser(phone, password)

        if user:
            token = userProcessor.createToken(user)
            res = Response(
                {
                    "code": 200,
                    "message": "성공"
                }
            )
            res.set_cookie("token", token, httponly=True)
            return res

    except KeyError:
        return Response({"code": 500, "message": "KEY_ERROR"}, status=500)

@api_view(['POST'])
def login(request):
    data = json.loads(request.body)

    phone = data['phone']
    password = data['password']
    user = User(phone, password)
    if user.exists():
        userProcessor = UserProcessor()
        token = userProcessor.createToken(user)
        response = Response(
            {
                "code": 200,
                "message": "login successs",
            }
        )

        response.set_cookie('token', token, httponly=True)
        return response
    else:
        return Response(
            {
                "code": 500,
                "message": "login fail",
            }
        )
@api_view(['POST'])
def logout(request):
    response = Response({
        "code": 200,
        "message" : "success"
    })
    response.delete_cookie('token')
    return response


@api_view(['POST'])
def createProduct(request):
    productProcessor = ProductProcessor()
    productProcessor.create(request)

    return Response({
        "code": 200,
        "message": "success"
    })
@api_view(['POST'])
def updateProduct(request, product_id):
    productProcessor = ProductProcessor()
    productProcessor.update(product_id, request)

    return Response({
        "code": 200,
        "message": "success"
    })
@api_view(['DELETE'])
def deleteProduct(request, product_id):
    productProcessor = ProductProcessor()
    productProcessor.delete(product_id)

    return Response({
        "code": 200,
        "message": "success"
    })