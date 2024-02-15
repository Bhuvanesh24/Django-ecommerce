from django.urls import path
from Zacapp import views

urlpatterns = [
    path('',views.index,name='index'),
    path('collections',views.collections,name='collections'),
    path('checkout', views.Checkout.as_view(), name='checkout'),
    path('verify_payment',views.verify_payment,name='verify_payment'),
    path('paymentsuccess/<str:user_order_id>',views.paymentsuccess,name='paymentsuccess'),
    path('paymentfailure',views.paymentfailure,name='paymentfailure'),
    path('razorpay1/<int:amount>/<str:user_order_id>',views.razorpay1,name='razorpay1'),
    path('orders',views.orders,name='orders'),
    path('tracker/<str:order_id>',views.tracker,name='tracker'),
    path('product/<int:product_id>',views.product,name='product'),
    path('add', views.add, name='add'),
    path('cart',views.cart,name='cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add-to-cart'),
]