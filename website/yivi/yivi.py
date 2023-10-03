import json

import requests


class YiviException(Exception):
    """Yivi Exception."""

    def __init__(self, http_status, code, msg, reason=None, headers=None):
        """Initialize Yivi Exception."""
        self.http_status = http_status
        self.code = code
        self.msg = msg
        self.reason = reason
        if headers is None:
            headers = {}
        self.headers = headers

    def __str__(self):
        """Convert this object to string."""
        return "http status: {0}, code:{1} - {2}, reason: {3}".format(
            self.http_status, self.code, self.msg, self.reason
        )


class Yivi:
    """Yivi class."""

    def __init__(self, prefix, token=None):
        """Initialize Yivi class."""
        self.prefix = prefix
        self.token = token

    def _auth_headers(self):
        """Get the authentication headers for a request."""
        if self.token is None:
            return dict()
        else:
            return {"Authorization": self.token}

    def _internal_call(self, method, url, payload, params):
        """Do an internal call."""
        args = {"params": params}

        if not url.startswith("http"):
            url = self.prefix + url

        headers = self._auth_headers()

        if "content_type" in args["params"]:
            headers["Content-Type"] = args["params"]["content_type"]
            del args["params"]["content_type"]
            if payload:
                args["data"] = payload
        else:
            headers["Content-Type"] = "application/json"
            if payload:
                args["data"] = json.dumps(payload)

        try:
            response = requests.request(method, url, headers=headers, **args)
            response.raise_for_status()
            results = response.json()
        except requests.exceptions.HTTPError as http_error:
            response = http_error.response
            try:
                json_response = response.json()
                reason = json_response.get("error", None)
                msg = json_response.get("description")
            except ValueError:
                reason = None
                msg = response.text or None
            raise YiviException(
                response.status_code,
                -1,
                "%s:\n %s" % (response.url, msg),
                reason=reason,
                headers=response.headers,
            )
        except requests.exceptions.RetryError as retry_error:
            request = retry_error.request
            try:
                reason = retry_error.args[0].reason
            except (IndexError, AttributeError):
                reason = None
            raise YiviException(429, -1, "%s:\n %s" % (request.path_url, "Max Retries"), reason=reason)
        except ValueError:
            results = None

        return results

    def _get(self, url, args=None, payload=None, **kwargs):
        """GET request."""
        if args:
            kwargs.update(args)

        return self._internal_call("GET", url, payload, kwargs)

    def _post(self, url, args=None, payload=None, **kwargs):
        """POST request."""
        if args:
            kwargs.update(args)
        return self._internal_call("POST", url, payload, kwargs)

    def _delete(self, url, args=None, payload=None, **kwargs):
        """DELETE request."""
        if args:
            kwargs.update(args)
        return self._internal_call("DELETE", url, payload, kwargs)

    def _put(self, url, args=None, payload=None, **kwargs):
        """PUT request."""
        if args:
            kwargs.update(args)
        return self._internal_call("PUT", url, payload, kwargs)

    def _patch(self, url, args=None, payload=None, **kwargs):
        """PATCH request."""
        if args:
            kwargs.update(args)
        return self._internal_call("PATCH", url, payload, kwargs)

    def start_session(self, payload):
        """Start a Yivi session."""
        return self._post("/session/", payload=payload)

    def session_status(self, token):
        """Get the session status of a session."""
        return self._get(f"/session/{token}/status")

    def session_result(self, token):
        """Get the session result."""
        return self._get(f"/session/{token}/result")
