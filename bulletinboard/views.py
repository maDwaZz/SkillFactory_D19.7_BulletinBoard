from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView
import string
import secrets

from .forms import *
from .models import *
from .utils import DataMixin

menu = [{'title': 'О сайте', 'url_name': 'about'},
        {'title': 'Обратная связь', 'url_name': 'contact'},
        ]


class PostList(DataMixin, ListView):
    model = Post
    template_name = 'bulletinboard/index.html'
    context_object_name = 'posts'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Главная страница')
        return context | c_def


class PostCategory(DataMixin, ListView):
    model = Post
    template_name = 'bulletinboard/index.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(category__slug=self.kwargs['cat_slug'])

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Категория - ' + str(context['posts'][0].category),
                                      cat_selected=context['posts'][0].category_id)
        return context | c_def


class AddPost(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddPostForm
    model = Post
    template_name = 'bulletinboard/addpost.html'
    success_url = reverse_lazy('home')
    login_url = reverse_lazy('home')
    raise_exception = True

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Создание нового поста')
        return context | c_def

    def form_valid(self, form):
        # Get the Author instance associated with the logged-in user
        author_instance, created = Author.objects.get_or_create(user=self.request.user)

        # Set the author field of the form instance to the Author instance
        form.instance.author = author_instance
        return super().form_valid(form)


class ShowPost(DataMixin, DetailView):
    model = Post
    template_name = 'bulletinboard/post.html'
    context_object_name = 'post'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title=context['post'], form=AddMessageForm())
        return context | c_def

    def get_object(self, queryset=None):
        post_id = self.kwargs.get('post_id')
        return get_object_or_404(Post, id=post_id)


def add_message(request, post_id):
    if request.method == 'POST':
        form = AddMessageForm(request.POST)
        if form.is_valid():
            # Save the comment
            post = Post.objects.get(id=post_id)
            author_instance, created = Author.objects.get_or_create(user=request.user)
            comment = Message(post=post, author=author_instance, text=form.cleaned_data['text'])
            comment.save()
    return redirect('message_sent')


def about(request):
    context = {'title': 'Страница о сайте', 'menu': menu}
    return render(request, template_name='bulletinboard/about.html', context=context)


def contact(request):
    context = {'title': 'Контакты', 'menu': menu}
    return render(request, template_name='bulletinboard/contact.html', context=context)


class ShowMessages(LoginRequiredMixin, DataMixin, ListView):
    model = Message
    template_name = 'bulletinboard/messages.html'
    context_object_name = 'messages'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Все полученные отклики')
        return context | c_def

    def get_queryset(self):
        author_instance, created = Author.objects.get_or_create(user=self.request.user)
        return Message.objects.filter(post__author_id=author_instance)


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'bulletinboard/register.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'bulletinboard/login.html'

    def generate_one_time_code(self, length=10):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация'
        return context

    def form_valid(self, form):
        def form_valid(self, form):
            # Call the parent class method to perform the default login logic
            response = super().form_valid(form)

            # Get the user object after form validation
            user = form.get_user()

            # Generate a one-time code
            one_time_code = generate_one_time_code()

            # Create an instance of the OneTimeCode model
            OneTimeCode.objects.create(one_time_code=one_time_code)

            # Send an email to the user with the one-time code
            subject = 'Your One-Time Code'
            message = f'Your one-time code is: {one_time_code}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            send_mail(subject, message, from_email, recipient_list)

            # Additional code for one-time code validation
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            entered_one_time_code = form.cleaned_data['one_time_code']

            user = authenticate(self.request, username=username, password=password)

            if user is not None:
                try:
                    code = OneTimeCode.objects.get(one_time_code=entered_one_time_code)
                    if code:
                        login(self.request, user)
                        code.delete()
                        return response
                except OneTimeCode.DoesNotExist:
                    pass

            return response


def logout_user(request):
    logout(request)
    return redirect('login')


@login_required
def approve_message(request, message_id):
    message = Message.objects.get(pk=message_id)
    message.is_approved = True
    message.save()
    return redirect('messages')


class MessageDelete(LoginRequiredMixin, DataMixin, DeleteView):
    model = Message
    template_name = 'bulletinboard/message_delete.html'
    success_url = reverse_lazy('messages')


def message_sent(request):
    context = {'title': 'Отклик успешно отправлен на подтверждение!', 'menu': menu}
    return render(request, template_name='bulletinboard/message_sent.html', context=context)
