from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
import string
import secrets

from .filters import MessageFilter
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

    def get_queryset(self):
        author_instance, created = Author.objects.get_or_create(user=self.request.user)
        queryset = super().get_queryset()
        self.filterset = MessageFilter(self.request.GET, queryset, user=self.request.user)
        # return Message.objects.filter(post__author_id=author_instance)
        return self.filterset.qs.filter(post__author=author_instance)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Все полученные отклики', filterset=self.filterset)
        return context | c_def


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'bulletinboard/register.html'
    success_url = reverse_lazy('login')

    def generate_one_time_code(self, length=10):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context

    def form_valid(self, form):
        # Generate a one-time code
        one_time_code = self.generate_one_time_code()

        # Send the one-time code via email
        subject = 'Ваш одноразовый код'
        message = f'Ваш одноразовый код для регистрации: {one_time_code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [form.cleaned_data['email']]

        send_mail(subject, message, from_email, recipient_list)

        # Save the user, but don't log them in yet
        user = form.save(commit=False)
        user.set_unusable_password()  # Set an unusable password
        user.save()
        self.request.session['register_username'] = user.username
        self.request.session['register_password'] = form.cleaned_data['password1']

        # Store the one-time code in session for validation
        self.request.session['one_time_code'] = one_time_code

        return redirect('verify_code')  # Redirect to the page where the user inputs the code


class VerifyCodeView(View):
    template_name = 'bulletinboard/verify_code.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        entered_code = request.POST.get('one_time_code')
        stored_code = request.session.get('one_time_code')

        if entered_code == stored_code:
            # If the code matches, proceed with user registration
            user = User.objects.get(username=request.session.get('register_username'))
            user.set_password(request.session.get('register_password'))  # Set the actual password
            user.save()

            # Log in the user
            login(request, user)

            # Clear the session data
            del request.session['one_time_code']
            del request.session['register_username']
            del request.session['register_password']

            return redirect('home')

        return render(request, self.template_name, {'error_message': 'Неверный код'})


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'bulletinboard/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация'
        return context


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


class PostUpdate(LoginRequiredMixin, DataMixin, UpdateView):
    form_class = AddPostForm
    model = Post
    template_name = 'bulletinboard/post_edit.html'
    permission_required = ('post.change_post',)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author.user != self.request.user:
            return HttpResponseForbidden("У вас нет доступа к редактированию этого поста.")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author.user != self.request.user:
            return HttpResponseForbidden("У вас нет доступа к редактированию этого поста.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Редактирование поста')
        return context | c_def


class PostDelete(LoginRequiredMixin, DataMixin, DeleteView):
    model = Post
    template_name = 'bulletinboard/post_delete.html'
    success_url = reverse_lazy('home')
    permission_required = ('post.delete_post',)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author.user != self.request.user:
            return HttpResponseForbidden("У вас нет доступа к удалению этого поста.")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author.user != self.request.user:
            return HttpResponseForbidden("У вас нет доступа к удалению этого поста.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Удаление поста')
        return context | c_def
