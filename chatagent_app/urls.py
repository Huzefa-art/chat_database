from django.urls import path
from . import views

urlpatterns = [
    path('send-message/', views.chat, name='send_message'),
    path('create-chat/', views.start_chat, name='create_chat'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.CreateTokenView.as_view(), name='login'),
    path('update-chat/<int:chat_id>/', views.manage_chat_session, name='update_chat'),
    path('delete-chat/<int:chat_id>/', views.manage_chat_session, name='delete_chat'),
    path('load-chathistory/', views.load_chathistory, name='load_chathistory'),
    path('list-chats/', views.list_chats, name='list_chats'),
]