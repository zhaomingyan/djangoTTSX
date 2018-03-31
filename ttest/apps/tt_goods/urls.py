from django.conf.urls import url
from . import views
urlpatterns=[
    url('^index$',views.index),
    url(r'^(\d+)$',views.detail),
    url(('^list(\d+)$'),views.list_sku),
]