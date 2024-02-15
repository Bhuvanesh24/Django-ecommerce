from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
#Activate Account
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.urls import NoReverseMatch,reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,DjangoUnicodeDecodeError
#email
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.mail import BadHeaderError,send_mail
from django.core import mail
from django.conf import settings
from django.core.mail import EmailMessage

from .utils import TokenGenerator,generate_token


from django.contrib.auth.tokens import PasswordResetTokenGenerator
# Create your views here.
import threading



class EmailThread(threading.Thread):
    def __init__(self, email_message):
        self.email_message=email_message
        threading.Thread.__init__(self)
    
    def run(self):
        self.email_message.send()

def signup(request): 
    if request.method == "POST":
        username = request.POST['name']
        email = request.POST['email']
        password1 = request.POST['pass']
        confirm_password = request.POST['re_pass']
        if password1!=confirm_password:
            messages.warning(request,"Password is Not Matching")
            return render(request,'auth/signup.html')
        try:
            if User.objects.get(username=username):
                messages.warning(request,"Username is Taken")
                return render(request,'auth/signup.html')
        except Exception as identifier:
            pass
        try:
            if User.objects.get(email=email):
                messages.warning(request,"Email is Taken")
                return render(request,'auth/signup.html')
        except Exception as identifier:
            pass
        
        user = User.objects.create_user(username,email,password1)
        user.is_active=False
        user.save()
        current_site = get_current_site(request)
        email_subject = "Activate Your Account"

        message = render_to_string('auth/activate.html',{
            'user':user,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':generate_token.make_token(user),
        })  
        email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email],)
        EmailThread(email_message).start()
        messages.info(request,"Activate your account by clicking the link on your email!")
        return redirect('login')
    
    return render(request, 'auth/signup.html')


def handlelogin(request):
    if request.method=="POST":
        usn=request.POST['name']
        esn=request.POST['email']
        psn=request.POST['pass']
        myuser=authenticate(username=usn,email=esn,password=psn)
        
        if myuser is not None:
            login(request,myuser)
            messages.success(request,"Login Success")
            return render(request,'index.html')
        
        else:
            messages.warning(request,"Invalid Credentials")
            return redirect('login')

    return render(request,'auth/login.html')


def handlelogout(request):
    logout(request)
    messages.info(request,"Logged Out Successfully")
    return redirect("login")

class ActivateAccountView(View):
    def get(self,request,uidb64,token):
        try:
            uid  = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception as identifier:
            user  = None
        if user is not None and generate_token.check_token(user,token):
            user.is_active=True
            user.save()
            messages.info(request,"Account Activated succesfully")
            return redirect('login')
        
        return render(request,'auth/activatefail.html')


class RequestResetEmailView(View):
    def get(self, request):
        return render(request, 'auth/request-reset-email.html')

    def post(self, request):
        email = request.POST['email']
        user = User.objects.filter(email=email)
        print(user)
        if user.exists():
            current_site = get_current_site(request)
            email_subject = '[Reset Your Password]'
            message = render_to_string('auth/reset-user-pass.html', {
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0]),
            })
            email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email])
            EmailThread(email_message).start()
            messages.info(request, "We have sent you an email to reset your password. Please check your inbox.")
            return render(request, 'auth/request-reset-email.html')
        else:
            messages.warning(request, "User with this email does not exist.")
            return render(request, 'auth/request-reset-email.html')

class SetNewPasswordView(View):
    def get(self,request,uidb64,token):
        context={
                'uidb64':uidb64,
                'token':token,
            }
        try:
            user_id = force_bytes(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user,token):
                messages.warning(request,"Password Reset Link Invalid")
                return render(request,'auth/request-reset-email.html')
            
        except DjangoUnicodeDecodeError as identifier:
            pass
        return render(request,'auth/set-new-password.html',context)
    
    def post(self,request,uidb64,token):
        context = {
            'uidb64':uidb64,
            'token':token,
        }

        password1 = request.POST['pass']
        confirm_password = request.POST['re_pass']
        if password1!=confirm_password:
            messages.warning(request,"Password is Not Matching")
            return render(request,'auth/set-new-password.html',context)
        
        try:
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            user.set_password(password1)
            user.save()
            messages.success(request,"Password reset success,Login with new Pass")
            return redirect('login')
        
        except DjangoUnicodeDecodeError as identifier:
            messages.error(request,"Something went Wrong")
            return render(request,'auth/set-new-password.html',context)
        
        return render(request,'auth/set-new-password.html',context)
    
       
    
