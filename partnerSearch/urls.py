# partners/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.partner_list, name='list'),                    # GET/POST all
    # path('<int:pk>/', views.partner_detail, name='detail'),       # single partner
    path('recommend/', views.recommend_partners, name='recommend'),  # ← THIS ONE
]