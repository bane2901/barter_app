from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Offers
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/<int:pk>/', views.offer_detail, name='offer_detail'),
    path('offers/create/', views.offer_create, name='offer_create'),
    path('offers/<int:pk>/edit/', views.offer_edit, name='offer_edit'),
    path('offers/<int:pk>/delete/', views.offer_delete, name='offer_delete'),
    path('my-offers/', views.my_offers, name='my_offers'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('user/<str:username>/', views.user_profile_view, name='user_profile_view'),

    # Messages
    path('messages/', views.my_messages, name='my_messages'),
    path('messages/<str:username>/', views.view_conversation, name='view_conversation'),
    path('send-message/<str:username>/', views.send_message, name='send_message'),

    # Trades
    path('trades/', views.my_trades, name='my_trades'),
    path('trades/<int:pk>/', views.trade_detail, name='trade_detail'),
    path('trades/<int:offer_id>/create/', views.create_trade, name='create_trade'),
    path('trades/<int:pk>/accept/', views.accept_trade, name='accept_trade'),
    path('trades/<int:pk>/accept-with-offer/<int:offer_id>/', views.accept_trade_with_offer, name='accept_trade_with_offer'),
    path('trades/<int:pk>/accept-buy/', views.accept_trade_buy, name='accept_trade_buy'),
    path('trades/<int:pk>/reject/', views.reject_trade, name='reject_trade'),
    path('trades/<int:pk>/complete/', views.complete_trade, name='complete_trade'),

    # Reviews
    path('reviews/<str:username>/', views.add_review, name='add_review'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='delete_notification'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # API Endpoints
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
    path('api/offer/<int:pk>/stats/', views.get_offer_stats, name='get_offer_stats'),
    path('api/user/<str:username>/stats/', views.get_user_stats, name='get_user_stats'),
    path('api/categories/', views.get_categories, name='get_categories'),
    path('api/search-offers/', views.search_offers, name='search_offers'),
    path('api/messages/', views.get_messages_list, name='get_messages_list'),
    path('api/trades/', views.get_trades_list, name='get_trades_list'),
    path('api/offer/<int:pk>/detail/', views.get_offer_detail_api, name='get_offer_detail_api'),
    path('api/user/<str:username>/detail/', views.get_user_detail_api, name='get_user_detail_api'),
]
