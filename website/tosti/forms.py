from django import forms
from oauth2_provider.forms import AllowForm
from oauth2_provider.models import Application
from oauth2_provider.scopes import get_scopes_backend


class OAuthCredentialsForm(forms.ModelForm):
    """OAuth Credentials Form."""

    class Meta:
        """Meta class for OAuth Credentials Form."""

        model = Application
        fields = [
            "name",
            "redirect_uris",
        ]


class GranularAuthorizationForm(AllowForm):
    """Consent form that lets the user pick which requested scopes to grant.

    The upstream ``AllowForm.scope`` is a hidden CharField — whatever the
    client asked for is granted wholesale. We override it with a
    ``MultipleChoiceField`` whose options are the scopes the client
    actually requested, and add a hidden ``requested_scope`` field that
    round-trips the original request through the POST so we can still
    validate the user's selection is a subset of what was asked for.

    The cleaned ``scope`` value is the space-joined subset the user
    ticked, which the upstream ``AuthorizationView.form_valid`` then
    forwards to ``create_authorization_response`` as the granted scope.
    """

    # Round-trip the originally-requested scopes through the form so the
    # POST handler knows what the legal choices were. Without this, a user
    # could craft a POST that grants an arbitrary scope by ticking a
    # checkbox the GET never offered.
    requested_scope = forms.CharField(widget=forms.HiddenInput())
    scope = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=True,
        error_messages={
            "required": "Select at least one permission, or click Cancel to deny.",
        },
    )

    def __init__(self, *args, **kwargs):
        # ``initial`` arrives as a space-separated string (from
        # AuthorizationView.get_initial); MultipleChoiceField wants a list
        # of codes, so split it before super() runs.
        initial = kwargs.get("initial", {}) or {}
        if isinstance(initial.get("scope"), str):
            initial = {
                **initial,
                "scope": initial["scope"].split(),
                "requested_scope": initial["scope"],
            }
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

        # The list of requested scopes comes from `initial["requested_scope"]`
        # on GET and from POST `data["requested_scope"]` on POST. Either way,
        # split it into codes and use as the choice set.
        requested = ""
        if self.is_bound:
            requested = self.data.get("requested_scope", "")
        if not requested:
            requested = self.initial.get("requested_scope", "")

        all_scopes = get_scopes_backend().get_all_scopes()
        self.fields["scope"].choices = [
            (code, all_scopes.get(code, code))
            for code in requested.split()
            if code in all_scopes
        ]

    def clean_scope(self):
        """Return the granted scopes as a space-separated string."""
        return " ".join(self.cleaned_data["scope"])
