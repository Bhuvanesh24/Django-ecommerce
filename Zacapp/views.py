from django.shortcuts import render,redirect
from .models import *
from math import ceil
from django.contrib import messages
# Create your views here.
import json
from django.http import JsonResponse
import os,base64
import hmac,uuid
import hashlib
from django.conf import settings
from .keys import *
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum,F
from django.shortcuts import get_object_or_404

def generate_signature(order_id, razorpay_payment_id, secret):
    message = f"{order_id}|{razorpay_payment_id}"
    secret_key = bytes(secret, 'utf-8')
    message = bytes(message, 'utf-8')
    signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    return signature


def index(request):
    return render(request,'index.html')

def generate_nonce():
    return base64.b64encode(os.urandom(32)).decode('utf-8')

def collections(request):
    current_user = request.user
    print(current_user)
    allProds = []
    catProds = Product.objects.values('category','id')
    cats = {item['category'] for item in catProds}
    for cat in cats:
        prod = Product.objects.filter(category = cat)
        n=len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        print(nSlides)
        allProds.append([prod,range(1,nSlides),nSlides])
    params = {'allProds':allProds}
    print(allProds)
    return render(request,'collections.html',params)


class Checkout(View):
    def get(self,request):
        nonce = generate_nonce()
        user_cart = Cart.objects.get(user=request.user) 
        cart_items = user_cart.cartitem_set.all()
        total_price = user_cart.total_amount
        context = {'nonce':nonce,'cart_items':cart_items,'total_amount':total_price}
        return render(request, 'checkout.html',context)
    @csrf_exempt
    def post(self, request):
        nonce = generate_nonce()
        context = {'nonce': nonce}
        user = request.user
        cart = Cart.objects.get(user=user)
        items_json = self.get_items_json(cart)
        amount = cart.total_amount
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order_id = generate_order_id()

        Order = Orders(order_id=order_id, items_json=items_json, name=name, amount=amount, email=email, address1=address1,
                       address2=address2, city=city, state=state, zip_code=zip_code, phone=phone)
        try:
            Order.save()
        except Exception as e:
            print("Error while making order", e)
            messages.error(request, "Error while processing the order. Please try again.")
            return redirect('collections')

        print(Order)
        amount_in_paise = int(amount)
        print(amount_in_paise)

        return redirect('razorpay1', amount=amount_in_paise, user_order_id=order_id)
    

    def get_items_json(self, cart):
        items = []
        for item in cart.cartitem_set.all():
            items.append({
                'product_name': item.product.product_name,
                'price': item.product.price,
                'quantity': item.quantity
            })
        return json.dumps(items)

@csrf_exempt
def verify_payment(request,*args, **kwargs):
    user_order_id = kwargs.get('user_order_id')
    print(user_order_id)
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        generated_signature = generate_signature(razorpay_order_id, razorpay_payment_id, razor_pay_secret)
        print("Generated Signature : ",generated_signature)
        print("Actual Signature: ",razorpay_signature)

        if generated_signature == razorpay_signature:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    

def razorpay1(request,*args, **kwargs):
    amount = int(kwargs.get('amount', ''))*100
    print('******')
    order_id =  kwargs.get('user_order_id','')
    print(amount)
    print(order_id)
    nonce = generate_nonce()
    client = razorpay.Client(auth=(razor_pay_id, razor_pay_secret))
    data = {"amount": amount, "currency": "INR", "receipt": "order_rcptid_11"}
    payment = client.order.create(data=data)
    context=({
            'api_key':razor_pay_id,
            'amount': payment['amount'],
            'order_id': payment['id'],
            'user_order_id':order_id
        })

    return render(request,'razorpay.html',context)

def paymentsuccess(request,user_order_id):
    if request.method=="POST":
        return redirect('tracker',order_id = user_order_id)
    print('*******')
    print(user_order_id)
    Order = Orders.objects.get(order_id = user_order_id)
    ConfirmedOrder = OrderUpdate(order_id=user_order_id)
    ConfirmedOrder.save()
    print(Order)
    Order.paymentstatus = "Paid"
    Order.save()
    return render(request,'paymentsucces.html')
    


def paymentfailure(request):
    return render(request,'paymentfailure.html')


def generate_order_id():
    order_id = uuid.uuid4()
    order_id_str = str(order_id).replace("-", "")
    return order_id_str



def tracker(request,order_id):
    order_id = order_id
    current_user1 = Orders.objects.get(order_id=order_id)
    current_user = OrderUpdate.objects.get(order_id=order_id)

    context = {
        'order_id':order_id,
        'created_at':current_user1.order_date,
        'update_desc':current_user.update_desc,
        'time':current_user.timestamp,
    }
    return render(request, 'tracker.html',context)


def orders(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Login & Try Again")
        return redirect('zacauth/login')
    
    username = request.user.email
    user_orders = Orders.objects.filter(email=username)

    orders_with_names = []
    for order in user_orders:
        try:
            order_list = json.loads(order.items_json)
            if isinstance(order_list, list):
                product_names = [item.get('product_name', '') for item in order_list]
                order_names = ', '.join(product_names)
                order_with_name = {'order': order, 'product_names': order_names}
                orders_with_names.append(order_with_name)
        except json.JSONDecodeError:
            # Handle invalid JSON in items_json field
            pass

    context = {"orders_with_names": orders_with_names}
    return render(request, 'order.html', context)


def product(request,product_id):
    product = Product.objects.get(id=product_id)
    return render(request,'product.html',{'product':product})

@login_required
@require_POST
def add(request):
    product_id = request.POST.get('product_id')
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            user_cart, _ = Cart.objects.get_or_create(user=request.user)
            # Try to get an existing CartItem object
            cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)
            # Increment the quantity if the CartItem exists
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            # Update the total amount in the cart
            user_cart.amount = user_cart.products.aggregate(Sum('price'))['price__sum']
            user_cart.save()
            return JsonResponse({'status': 'success'})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    

def cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.cartitem_set.all()
        total_quantity = sum(item.quantity for item in cart_items)
    else:
        cart_items = []
        total_quantity = 0

    context = {
        'cart_items': cart_items,
        'total_quantity': total_quantity,
    }
    return render(request, 'cart.html', context)
    

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.add_product(product)
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = Cart.objects.get(user=request.user)
    cart.remove_product(product)
    return redirect('cart')

