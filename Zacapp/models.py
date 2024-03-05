from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Product(models.Model):
    product_id = models.AutoField
    product_name = models.CharField(max_length=50)
    category = models.CharField(max_length = 50,default = 'Men')
    subcategory = models.CharField(max_length=75)
    price = models.IntegerField()
    desc = models.CharField(max_length=150)
    image = models.ImageField(upload_to='shop/images',default='')
    image2 = models.ImageField(upload_to='shop/images',default='')
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]

    size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='M')

    
    def __str__(self):
        return self.product_name

class Orders(models.Model):
    order_id = models.CharField(max_length=100,blank=True)
    items_json =  models.CharField(max_length=5000)
    amount = models.IntegerField(default=0)
    name = models.CharField(max_length=90)
    email = models.CharField(max_length=90)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)
    phone = models.CharField(max_length=100,default="")
    paymentstatus=models.CharField(max_length=20,blank=True,default="NotPaid")
    order_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class OrderUpdate(models.Model):
    update_id = models.AutoField(primary_key=True)
    order_id = models.CharField(max_length=100)
    update_desc = models.CharField(max_length=5000,default="OrderPlaced")
    timestamp = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.update_desc[0:7] + "..."
    

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def add_product(self, product,size='M', quantity=1):
        cart_item, created = CartItem.objects.get_or_create(cart=self, product=product, size=size)
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item.quantity = quantity  # Set the quantity if it's a new item
            cart_item.save()

    def remove_product(self, product,size='M'):
        try:
            cart_item = CartItem.objects.get(cart=self, product=product, size=size)
            if cart_item.quantity == 1:
                cart_item.delete()
            else:
                cart_item.quantity -= 1
                cart_item.save()
        except CartItem.DoesNotExist:
            pass

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=2, choices=Product.SIZE_CHOICES, default='M')

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} ({self.size}) in {self.cart}"
    

    @property
    def total_price(self):
        return self.quantity * self.product.price





