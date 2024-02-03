from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from django.conf import settings
import itertools
import aspose.barcode as barcode
import mysql.connector
import datetime
import bcrypt
import jwt
from pathlib import Path
import os


config = {
  'user': 'root',
  'password': '1234',
  'host': '127.0.0.1',
  'database': 'caffe'
}

class DBConnection:
    def connectToMysql(self, config):
        try:
            return mysql.connector.connect(**config)
        except (mysql.connector.Error, IOError) as err:
            print("Failed to insert into MySQL table {}".format(err))

class DictFetch:

    def __init__(self, cursor):
        self.cursor = cursor

    def dictFetchAll(self):
        columns = [col[0] for col in self.cursor.description]
        return [
            dict(zip(columns, row))
            for row in self.cursor.fetchall()
        ]

    def dictFetchOne(self):
        record = self.cursor.fetchone()
        return [
            dict(zip([c[0] for c in self.cursor.description], record))
        ]

class ProductProcessor:
    def __init__(self):
        self.connection = DBConnection().connectToMysql(config)

    def create(self, request):
        product_name = request.POST['product_name']
        category_id = request.POST['category_id']
        price = request.POST['price']
        wonga = request.POST['wonga']
        #qty = request.POST['qty']
        limit_date = request.POST['limit_date']
        description = request.POST['description']
        sizeList = request.POST.getlist('size_'+category_id)
        colorList = request.POST.getlist('color_'+category_id)

        product = Product(category_id, '', '', product_name, description)
        product_id, product_code = product.createProduct()
        barcode = BarCode(product_id, product_code)
        barcode.creaeteCode()

        price = Price(product_id, wonga, price)
        price.createPrice()

        if sizeList is not None:
            productOptionKind = ProductOptionKind('', product_id, 'size')
            productOptionKind.createOptionKind()

        if colorList is not None:
            productOptionKind = ProductOptionKind('', product_id, 'color')
            productOptionKind.createOptionKind()

        for color in list(colorList):
            for size in list(sizeList):
                option_name = color + '^' + size
                print(option_name)
                productOption = ProductOption(product_id, '', option_name)
                option_id = productOption.createOption()
                stock = Stock(product_id, option_id, 1, limit_date)
                stock.createStock()

    def update(self, product_id, request):
        product_name = request.POST['product_name']
        description = request.POST['description']
        price = request.POST['price']
        wonga = request.POST['wonga']
        product = Product('', product_id, '', product_name, description)
        product.updateProduct()
        price = Price(product_id, wonga, price)
        price.updatePrice()
        wongaHistory = WongaHistory('', wonga, datetime.datetime.utcnow())
        wongaHistory.createWongaHist(product_id, wonga)

    def delete(self, product_id):
        product = Product('', product_id, '', '', '')
        product.deleteProduct()
        price = Price(product_id, '', '')
        price.deletePrice()
        wongaHistory = WongaHistory(product_id, '', '')
        wongaHistory.deleteWongaHistory()
        productOptionKind = ProductOptionKind('', product_id, '')
        productOptionKind.deleteProductOptionKind()
        productOption = ProductOption(product_id, '', '')
        productOption.deleteOption()
        stock = Stock(product_id, '', 1, '')

class SearchProcessor:
    def __init__(self):
        self.connection = DBConnection().connectToMysql(config)

    def searchProducts(self, request):
        currentPage = request.GET['currentPage']
        pageSize = request.GET['pageSize']
        keyword = request.GET['keyword']

        startOffset = (int(currentPage) - 1) * int(pageSize)
        totalRecord = ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', )
        record = ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', startOffset, pageSize)
        cursor = self.connection.cursor(prepared=True)

        if keyword != '':
            cursor.execute("SELECT "
                     "  count(*) "
                     "FROM "
                     "  coffeeadmin_product"
                     "  INNER JOIN product_search ON coffeeadmin_product.product_id = product_search.product_id AND "
                     "      (LOWER(product_search.product_name) LIKE LOWER(%s) OR "
                     "      LOWER(product_search.product_code) LIKE LOWER(%s) OR "
                     "      LOWER(product_search.description) LIKE LOWER(%s) OR "
                     "      LOWER(product_search.size_list) LIKE LOWER(%s) OR "
                     "      LOWER(product_search.color_list) LIKE LOWER(%s) OR "
                     "      LOWER(product_search.price) >= %s )", totalRecord)
        else:
            cursor.execute("SELECT  "
                     "count(*) "
                     "FROM "
                     "  coffeeadmin_product")

        count = cursor.fetchone()

        if keyword != '':
            cursor.execute("SELECT "
                       "coffeeadmin_product.product_id, "
                       "coffeeadmin_product.product_name, "
                       "coffeeadmin_product.category_id, "
                       "coffeeadmin_product.product_code, "    
                       "price "
                       "FROM "
                       "  coffeeadmin_product "
                       "  INNER JOIN product_search ON coffeeadmin_product.product_id = product_search.product_id AND "
                       "      (LOWER(product_search.product_name) LIKE LOWER(%s) OR "
                       "      LOWER(product_search.product_code) LIKE LOWER(%s) OR "
                       "      LOWER(product_search.description) LIKE LOWER(%s) OR "
                       "      LOWER(product_search.size_list) LIKE LOWER(%s) OR "
                       "      LOWER(product_search.color_list) LIKE LOWER(%s) OR "
                       "      LOWER(product_search.price) LIKE LOWER(%s))"
                       "limit %s, %s", record)
        else:
            cursor.execute("SELECT  "
                            "   coffeeadmin_product.product_id, "
                            "   coffeeadmin_product.product_name, "
                            "   coffeeadmin_product.category_id, "
                            "   coffeeadmin_product.product_code, "   
                            "   price "
                            "FROM "
                            "  coffeeadmin_product"
                           "   left outer join coffeeadmin_price on coffeeadmin_product.product_id = coffeeadmin_price.product_id "
                           "limit %s, %s", (startOffset, pageSize, ))

        result = DictFetch(cursor).dictFetchAll()
        return {'total': count[0], 'products': result, 'currentPage': currentPage}

    def searchAddInfo(self):
        cursor = self.connection.cursor(prepared=True)
        cursor.execute("select "
                       "    cc.category_id, "
                       "    cc.category_name, "
                       "    size.size_name, "
                       "    color.color_name "
                       "from "
                       "    coffeeadmin_category cc "
                       "    left outer join ("
                       "        select"
                       "            cc.category_id, "
                       "            group_concat(cs.size_name) as size_name "
                       "        from "
                       "            coffeeadmin_size cs "
                       "            inner join coffeeadmin_category cc on cs.category_id = cc.category_id "
                       "        group by cs.category_id"
                       "    ) size on size.category_id = cc.category_id "
                       "    left outer join ( "
                       "        select "
                       "            cc.category_id, "
                       "            group_concat(cc.color_name) as color_name "
                       "        from "
                       "            coffeeadmin_color cc "
                       "            inner join coffeeadmin_category cc2 on cc.category_id = cc2.category_id "
                       "        group by cc.category_id "
                       "    ) color on color.category_id = cc.category_id"
                       )

        record = DictFetch(cursor).dictFetchAll()
        return record

class UserProcessor:
    def __init__(self):
        self.connection = DBConnection().connectToMysql(config)

    def createUser(self, phone, password):
        hashed_password = bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt()).decode()
        record = (phone, hashed_password, datetime.datetime.now(), datetime.datetime.now())
        cursor = self.connection.cursor()
        cursor.execute('insert into user(phone, password, created_at, updated_at) values(%s, %s, %s, %s)', record)
        self.connection.commit()
        user = User(phone, password)
        return user

    def createToken(self, user):
        token = jwt.encode({'phone': user.phone}, settings.SECRET_KEY, algorithm='HS256')
        return 'jwt ' + token

class User(AbstractBaseUser):
    phone = models.CharField(max_length=11, blank=True)
    password = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, phone, password):
        self.phone = phone
        self.password = password
        self.connection = DBConnection().connectToMysql(config)

    def exists(self):
        cursor = self.connection.cursor(prepared=True)
        cursor.execute("select phone, password from user where phone = %s", (self.phone, ))
        record = cursor.fetchone()

        print(cursor.rowcount)
        if cursor.rowcount == 0:
            return False
        else:
            if bcrypt.checkpw(self.password.encode('utf8'), record[1].encode('utf8')):
                return True

    def isUser(self):
        cursor = self.connection.cursor()
        cursor.execute("select phone, password from user where phone = %s", [self.phone])
        record = cursor.fetchone()

        if cursor.rowcount == 0:
            return False
        else:
            return True

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['phone']

    class Meta:
        db_table = 'User'

class Category(models.Model):
    p_category_id = models.CharField(max_length=9, null=True)
    category_id = models.CharField(max_length=9, primary_key=True)
    category_name = models.CharField(max_length=100)

class Size(models.Model):
    size_id = models.IntegerField(primary_key=True)
    category_id = models.CharField(max_length=9)
    size_name = models.CharField(max_length=100)

class Color(models.Model):
    color_id = models.IntegerField(primary_key=True)
    category_id = models.CharField(max_length=9)
    color_name = models.CharField(max_length=100)

class Product(models.Model):
    category_id = models.CharField(max_length=9)
    product_id = models.CharField(max_length=50, primary_key=True)
    product_code = models.CharField(max_length=50)
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    connection = DBConnection().connectToMysql(config)

    def createProduct(self):
        code = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        product_id = 'PRD' + code
        product_code = 'PCD' + code
        record = (self.category_id, self.product_name, self.description, product_id, product_code)
        cursor = self.connection.cursor()
        cursor.execute('insert into coffeeadmin_product(category_id, product_name, description, product_id, product_code) values(%s, %s, %s, %s, %s)', record)
        self.connection.commit()
        return (product_id, product_code)

    def updateProduct(self):
        record = (self.product_name, self.description, self.product_id)
        cursor = self.connection.cursor()
        cursor.execute(
            'update coffeeadmin_product set product_name = %s , description = %s where product_id = %s ',
            record)
        self.connection.commit()

    def deleteProduct(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_product where product_id = %s ',
            record)
        self.connection.commit()
    def getInfo(self):
        cursor = self.connection.cursor(prepared=True)
        cursor.execute(
               "select "
                       "    cp.product_id, "
                       "    product_name, "
                       "    category_id, "
                       "    product_code, "
                       "    price, "
                       "    wonga, "
                       "    description, "
                       "    list.size_list,  "
                       "    list.color_list, "
                       "    (select date_format(limit_date, '%Y-%m-%d') from coffeeadmin_stock where product_id = cp.product_id limit 1) as limit_date "
                       "from "
                       "    coffeeadmin_product cp "
                       "    inner join coffeeadmin_price p on cp.product_id = p.product_id "
                       "    left outer join ("
                       "        select "
                       "            cp.product_id, "
                       "            group_concat(distinct  substring_index(option_name,'^',1)) as color_list, "
                       "            group_concat(distinct  substring_index(option_name,'^',-1)) as size_list "
                       "        from "
                       "            coffeeadmin_product cp "
                       "            left outer join coffeeadmin_productoption cpp on cp.product_id = cpp.product_id "
                       "            group by "
                       "                cp.product_id"
                       "    ) list on list.product_id = cp.product_id "
                       "where "
                       " cp.product_id = %s ", [self.product_id])

        record = cursor.fetchone()
        return dict(zip([c[0] for c in cursor.description], record))

class ProductCode(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True)
    product_code = models.CharField(max_length=50)

class BarCode(ProductCode):

    connection = DBConnection().connectToMysql(config)

    def __init__(self, product_id, product_code):
        super().__init__(product_id, product_code)

    def creaeteCode(self):
        record = (super().product_code, super().product_id)
        cursor = self.connection.cursor()
        cursor.execute(
            'insert into coffeeadmin_productcode(product_code, product_id) values(%s, %s)', record)
        self.connection.commit()

        generator = barcode.generation.BarcodeGenerator(barcode.generation.EncodeTypes.CODE128, "test")
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        BARCODE_DIR = BASE_DIR + '/static/barcode/'
        generator.save(BARCODE_DIR + super().product_code)

class Price(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True)
    wonga = models.IntegerField()
    price = models.IntegerField()
    connection = DBConnection().connectToMysql(config)

    def createPrice(self):
        record = (self.product_id, self.price, self.wonga)
        cursor = self.connection.cursor(prepared=True)
        cursor.execute(
            'insert into coffeeadmin_price(product_id, price, wonga) values(%s, %s, %s)', record)
        self.connection.commit()

    def updatePrice(self):
        record = (self.price, self.wonga, self.product_id)
        cursor = self.connection.cursor()
        cursor.execute(
            'update coffeeadmin_price set price = %s, wonga = %s where product_id = %s ',record)
        self.connection.commit()

    def deletePrice(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_price where product_id = %s ',
            record)
        self.connection.commit()

class WongaHistory(models.Model):
    product_id = models.CharField(max_length=50)
    wonga = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)
    connection = DBConnection().connectToMysql(config)
    def createWongaHist(self, product_id, wonga):
        record = (product_id, wonga, datetime.datetime.utcnow())
        cursor = self.connection.cursor()
        cursor.execute(
            'insert into coffeeadmin_wongahistory(product_id, wonga, date) values(%s, %s, %s)', record)
        self.connection.commit()

    def deleteWongaHistory(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_wongahistory where product_id = %s ',
            record)
        self.connection.commit()

class ProductOptionKind(models.Model):
    product_id = models.CharField(max_length=50)
    kind_name = models.CharField(max_length=50)
    connection = DBConnection().connectToMysql(config)
    def createOptionKind(self):
        record = (self.product_id, self.kind_name)
        cursor = self.connection.cursor()
        cursor.execute('insert into coffeeadmin_productoptionkind(product_id, kind_name) values(%s, %s)', record)

        self.connection.commit()

    def deleteProductOptionKind(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_productoptionkind where product_id = %s ',
            record)
        self.connection.commit()

class ProductOption(models.Model):
    product_id = models.CharField(max_length=50)
    product_option_id = models.CharField(max_length=50, primary_key=True)
    option_name = models.CharField(max_length=100)
    connection = DBConnection().connectToMysql(config)

    def createOption(self):
        code = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        option_id = 'OPT' + code
        record = (option_id, self.product_id, self.option_name)
        cursor = self.connection.cursor()
        cursor.execute('insert into coffeeadmin_productoption(product_option_id, product_id, option_name) values(%s, %s, %s)', record)
        self.connection.commit()
        return option_id

    def deleteOption(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_productoption where product_id = %s ',
            record)
        self.connection.commit()

class Stock(models.Model):
    product_id = models.CharField(max_length=50)
    product_option_id = models.CharField(max_length=50, primary_key=True)
    qty = models.IntegerField()
    limit_date = models.DateField()
    connection = DBConnection().connectToMysql(config)
    def createStock(self):
        record = (self.product_id, self.product_option_id, self.qty, datetime.datetime.utcnow())
        cursor = self.connection.cursor()
        cursor.execute('insert into coffeeadmin_stock(product_id, product_option_id, qty, limit_date) values(%s, %s, %s, %s)', record)

        self.connection.commit()

    def deleteStock(self):
        record = (self.product_id, )
        cursor = self.connection.cursor()
        cursor.execute(
            'delete from coffeeadmin_stock where product_id = %s ',
            record)
        self.connection.commit()