from django.contrib.auth.decorators import login_required
from django.views.generic import View

class LoginRequiredMinix(object):
  """验证用户是否登陆"""
  @classmethod
  def as_view(cls, **initkwargs):
      # 自定义的as_view()方法中，调用父类的as_view()方法
      view = super().as_view()
      return login_required(view)