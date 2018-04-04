from django.shortcuts import render,redirect
from django.views.generic import View
from .models import User,Address,AreaInfo
from django.http import HttpResponse,JsonResponse
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from utils.views import LoginRequiredMinix
from django_redis import get_redis_connection
from tt_goods.models import GoodsSKU
import json


class RegisterView(View):
    def get(self,request):
        return render(request,'register.html')


    def post(self,request):
        #接受结果
        dict = request.POST
        uname = dict.get('uname')
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
        user.is_active = True
        user.save()





        # serializer = Serializer(settings.SECRET_KEY,60*60*7)
        # value = serializer.dumps({'id':user.id}).decode()
        #
        #
        # msg = '<a href="http://127.0.0.1:8000/user/active/%s">点击激活</a>' % value
        # send_mail('天天生鲜_激活地址','',settings.EMAIL_FROM,[email],html_message=msg)

        def send_active_email(email, uname, token):
            """封装发送邮件方法"""
            subject = "天天生鲜用户激活"  # 标题
            body = ""  # 文本邮件体
            sender = settings.EMAIL_FROM  # 发件人
            receiver = [email]  # 接收人
            html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                        '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                        'http://127.0.0.1:8000/users/active/%s</a></p>' % (uname, token, token)
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
        uname = request.COOKIES.get('uname','')
        context = {
            'title':'登录',
            'username':uname,
        }
        return render(request,'login.html',context)
    def post(self,request):
        #接收数据
        dict = request.POST
        uname = dict.get('username')
        pwd = dict.get('pwd')
        remember = dict.get('remember')

        context = {
            'username':uname,
            'pwd':pwd,
            'err_msy':''
        }
        #判断数据是否为空
        if not all([uname ,pwd]):
            context['err_msy'] = '请填写帐号和密码'
            return render(request,'login.html',context)
        # 判断数据是否存在
        user = authenticate(username=uname, password=pwd)

        if user is None:
            context['err_msy'] = '用户名和密码错误'
            return render(request,'login.html',context)

        if user.is_active is False:
            context['err_msy'] = '请先到邮箱激活'
            return render(request,'login.html',context)


        #状态保持
        login(request,user)

       # next
        next_url = request.GET.get('next','/user/info')
        response = redirect(next_url)

        #记住用户名
        if remember is None:
            response.delete_cookie('uname')
        else:
            response.set_cookie('uname',uname,expires=60*60*24*7)

        #读取购物车中的信息，转成字典
        cart_str=request.COOKIES.get('cart')
        if cart_str:
            # 将cookie中的购物车信息，转存入redis中
            #构造键
            key = 'cart%d' % request.user.id
            #链接redis
            redis_client = get_redis_connection()

            cart_dict=json.loads(cart_str)
            for k,v in cart_dict.items():
                #判断redies中是否已经存在这个商品
                if redis_client.hexists(key,k):
                    #如果有，则数量相加
                    count1=int(redis_client.hget(key,k))
                    count2=v
                    count0=count1+count2
                    if count0>5:
                        count0=5
                    redis_client.hset(key,k,count0)
                else:
                    #如果没有，则添加
                    redis_client.hset(key,k,v)

            #已经成功转存到redis，删除cookie中的信息
            response.delete_cookie('cart')

        #返回用户中心首页

        return response


def logout_user(request):
    logout(request)
    return redirect('/user/login')


#个人信息
@login_required
def info(request):
    # 查询当前用户的默认收货地址,如果没有数据则返回[]
    adderss = request.user.address_set.filter(isDefault=True)
    if adderss:
        adderss = adderss[0]
    else:
        adderss=None
    # 获取redis服务器的连接,根据settings.py中的caches的default获取
    redis_client = get_redis_connection()
    # 因为redis中会存储所有用户的浏览记录，所以在键上需要区分用户
    gid_list = redis_client.lrange('history%d' % request.user.id, 0, -1)
    # 根据商品编号查询商品对象
    goods_list = []
    for gid in gid_list:
        goods_list.append(GoodsSKU.objects.get(pk=gid))

    context={
        'adderss':adderss,
        'goods_list': goods_list
    }
    return render(request,'user_center_info.html',context)


#全部订单
@login_required
def order(request):
    context = {}
    return render(request, 'user_center_order.html',context)


#收获地址
class SiteView(LoginRequiredMinix,View):

    def get(self,request):
        addr_list = Address.objects.filter(user=request.user)
        context={
            'title':'收货地址',
            'addr_list':addr_list,
        }
        return render(request,'user_center_site.html',context)
    def post(self,request):
        #接收数据
        dict = request.POST
        receiver = dict.get('receiver')
        province = dict.get('province')
        city = dict.get('city')
        district = dict.get('district')
        addr = dict.get('addr')
        code = dict.get('code')
        phone = dict.get('phone')
        default = dict.get('default')

        #判断数据
        if not all([receiver,province,city,district,addr,code,phone]):
            return render(request,'user_center_site.html',{'err_msy':'请完整填写信息'})

        #保存数据
        addrss = Address()
        addrss.receiver = receiver
        addrss.province_id = province
        addrss.city_id = city
        addrss.district_id = district
        addrss.addr = addr
        addrss.code = code
        addrss.phone_number = phone
        if default:
            addrss.isDefault = True
        addrss.user = request.user
        addrss.save()


        #返回结果
        return redirect('/user/site')


def area(request):
    pid = request.GET.get('pid')

    if pid is None:
        #查询省信息
        slist = AreaInfo.objects.filter(aParent__isnull=True)
    else:
        slist = AreaInfo.objects.filter(aParent_id=pid)
    #将数据结构整理为：[{id:***,title:***}]
    slist2 = []
    for s in slist:
        slist2.append({'id':s.id,'title':s.title})
    #
    return JsonResponse({'list':slist2})



