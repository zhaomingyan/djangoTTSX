from django.conf.urls import url
from . import views
urlpatterns=[
    url('^register$',views.RegisterView.as_view()),
    url('^active/(.+)$',views.active),
    url('^login$',views.LoginView.as_view()),
]