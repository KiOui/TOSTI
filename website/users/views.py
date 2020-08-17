from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import LoginForm, AccountForm
from .services import get_openid_verifier, update_staff_status


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
        if request.user.is_authenticated:
            if request.GET.get("next"):
                return redirect(request.GET.get("next"))
            else:
                return redirect("users:account")

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

        if request.user.is_authenticated:
            if request.GET.get("next"):
                return redirect(request.GET.get("next"))
            else:
                return redirect("users:account")

        if form.is_valid():
            openid_verifier = get_openid_verifier(request)
            verify_url = openid_verifier.get_request_url(form.cleaned_data.get("username"))
            response = redirect(verify_url)
            if form.cleaned_data.get("remember"):
                response.set_cookie(self.remember_cookie, form.cleaned_data.get("username"))
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
        openid_verifier = get_openid_verifier(request)
        user = openid_verifier.extract_user()
        if user:
            update_staff_status(user)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            next_page = request.GET.get("next")
            if next_page:
                return redirect(next_page)

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


class AccountView(LoginRequiredMixin, TemplateView):
    """Account view."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """
        GET request for the account view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the account view
        """
        form = AccountForm(
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "username": request.user.username,
                "email": request.user.email,
            }
        )
        return render(request, self.template_name, {"form": form})
