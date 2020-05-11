from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from .forms import LoginForm
from .services import get_openid_request_url, get_full_user_id
from django.conf import settings
from .services import verify_request

User = get_user_model()


class LoginView(TemplateView):
    """Login view."""

    template_name = "users/login.html"

    remember_cookie = "_remembered_username"

    def get(self, request, **kwargs):
        """
        GET request for the login view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the login view
        """
        form = LoginForm()
        remembered_username = request.COOKIES.get(self.remember_cookie, None)
        if remembered_username is not None:
            form.fields["username"].initial = remembered_username

        return render(request, self.template_name, {"form": form})

    def post(self, request, **kwargs):
        """
        POST request for the login view.

        Redirects a user to the OpenID verification server.
        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to the OpenID verification server if the LoginForm is valid, a render of the login page
        otherwise
        """
        form = LoginForm(request.POST)

        if form.is_valid():
            full_username = get_full_user_id(form.cleaned_data.get("username"))
            verify_url = get_openid_request_url(
                settings.OPENID_SERVER_ENDPOINT,
                request.build_absolute_uri(reverse(settings.OPENID_RETURN_URL)),
                request.META["HTTP_HOST"],
                full_username,
            )
            response = redirect(verify_url)
            if form.cleaned_data.get("remember"):
                response.set_cookie(
                    self.remember_cookie, form.cleaned_data.get("username")
                )
            return response

        return render(request, self.template_name, {"form": form})


class VerifyView(TemplateView):
    """Verify view."""

    template_name = "users/verify.html"

    def get(self, request, **kwargs):
        """
        GET request for verify view.

        This view will verify if the given signature is valid against the OpenID server endpoint.
        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to the index page with the user logged in if the signature is valid, a render of an error
        page otherwise
        """
        username = verify_request(
            settings.OPENID_SERVER_ENDPOINT, request.get_full_path()
        )
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create(username=username)
            login(request, user)
            return redirect("index")

        return render(request, self.template_name)


class LogoutView(TemplateView):
    """Logout view."""

    template_name = "users/logout.html"

    def get(self, request, **kwargs):
        """
        GET request for the logout view.

        This view logs out a user
        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to the home page if a user is not logged in, redirects to the next GET parameter if it is
        set, returns a render of the logout page otherwise
        """
        next_page = request.GET.get("next")
        if request.user.is_authenticated:
            logout(request)
            if next_page:
                return redirect(next_page)
            return render(request, self.template_name)
        else:
            if next_page:
                return redirect(next_page)
            return redirect("/")
