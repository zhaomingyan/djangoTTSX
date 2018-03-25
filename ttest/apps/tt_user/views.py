from django.shortcuts import render,redirect
from django.views.generic import View
from .models import User
from django.http import HttpResponse
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login


class RegisterView(View):
    def get(self,request):
        return render(request,'register.html')


    def post(self,request):
        #接受结果
        dict = request.POST
        uname = dict.get('user_name')
        pwd = dict.get('pwd')
        cpwd = dict.get('cpwd')
        email = dict.get('email')
        uallow = dict.get('allow')


        #返回结果
        context = {
            'uname':uname,
            'pwd':pwd,
            'email':email,
            'cpwd': cpwd,
            'err_msy':'',
        }

        #判断结果是否为空
        if not uallow:
            context['err_msy']= '请同意协议'
            return render(request,'register.html',context)

        if not all([uname,pwd,cpwd,email]):
            context['err_msy']= '请填写正确信息'
            return render(request,'register.html',context)

        if pwd != cpwd:
            context['err_msy']= '两次密码不一致'
            return render(request,'register.html',context)

        if User.objects.filter(username=uname).count() > 0:
            context['err_msy']= '用户名已经存在'
            return render(request,'register.html',context)

        # if User.objects.filter(email=email).count()>0:
        #     context['err_msy']= '邮箱已经存在'
        #     return render(request,'register.html',context)


        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            context['err_msy']= '请正确填写邮箱'
            return render(request,'register.html',context)


        #保存数据
        user = User.objects.create_user(uname,email,pwd)
        user.is_active = False
        user.save()





        # serializer = Serializer(settings.SECRET_KEY,60*60*7)
        # value = serializer.dumps({'id':user.id}).decode()
        #
        #
        # msg = '<a href="http://127.0.0.1:8000/user/active/%s">点击激活</a>' % value
        # send_mail('天天生鲜_激活地址','',settings.EMAIL_FROM,[email],html_message=msg)

        def send_active_email(email, user_name, token):
            """封装发送邮件方法"""
            subject = "天天生鲜用户激活"  # 标题
            body = ""  # 文本邮件体
            sender = settings.EMAIL_FROM  # 发件人
            receiver = [email]  # 接收人
            html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                        '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                        'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
            send_mail(subject, body, sender, receiver, html_message=html_body)


        return HttpResponse('注册成功')


def active(request,value):
    #解密
    try:
        serializer = Serializer(settings.SECRET_KEY)
        dict = serializer.loads(value)
    except SignatureExpired as e:
        return HttpResponse('链接已过期')
    #激活指定账户
    uid = dict.get('id')
    user = User.objects.get(pk=uid)
    user.is_active = True
    user.save()

    return  redirect('/user/login')


class LoginView(View):
    def get(self,request):
        return render(request,'login.html')
    def post(self,request):
        #接收数据
        dict = request.POST
        user_name = dict.get('username')
        pwd = dict.get('pwd')

        context = {
            'username':user_name,
            'pwd':pwd,
            'err_msy':''
        }
        #判断数据是否为空
        if not all([user_name ,pwd]):
            context['err_msy'] = '请填写帐号和密码'
            return render(request,'login.html',context)
        # 判断数据是否存在
        user = authenticate(username=user_name, password=pwd)

        if user is None:
            context['err_msy'] = '用户名和密码错误'
            return render(request,'login.html',context)

        if user.is_active is False:
            context['err_msy'] = '请先到邮箱激活'
            return render(request,'login.html',context)


        #状态保持
        login(request,user)

        #返回用户中心首页

        return redirect('/user/info')
