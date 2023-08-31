from django.urls import path
from .views import *

urlpatterns = [
    path('', PostList.as_view(), name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('post/<int:post_id>', ShowPost.as_view(), name='post'),
    path('post/<int:pk>/update', PostUpdate.as_view(), name='post_edit'),
    path('post/<int:pk>/delete', PostDelete.as_view(), name='post_delete'),
    path('addpost/', AddPost.as_view(), name='add_post'),
    path('post/<int:post_id>/addmessage/', add_message, name='add_message'),
    path('messages/', ShowMessages.as_view(), name='messages'),
    path('messages/<int:message_id>/approve/', approve_message, name='approve_message'),
    path('messages/<int:pk>/delete/', MessageDelete.as_view(), name='message_delete'),
    path('messages/sent', message_sent, name='message_sent'),
    path('category/<slug:cat_slug>/', PostCategory.as_view(), name='category'),
    path('login/', LoginUser.as_view(), name='login'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('logout/', logout_user, name='logout'),
]
