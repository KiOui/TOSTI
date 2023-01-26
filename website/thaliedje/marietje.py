import base64
import json
import errno
import logging
import time

import requests
import urllib3
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class MarietjeOauthError(Exception):
    """Error during Auth Code or Implicit Grant flow."""

    def __init__(self, message, error=None, error_description=None, *args, **kwargs):
        """Initialize Marietje OAuth Error."""
        self.error = error
        self.error_description = error_description
        self.__dict__.update(kwargs)
        super(MarietjeOauthError, self).__init__(message, *args)


class MarietjeException(Exception):
    """Marietje Exception class."""

    def __init__(self, http_status, code, msg, reason=None, headers=None):
        """Initialize Marietje Exception."""
        self.http_status = http_status
        self.code = code
        self.msg = msg
        self.reason = reason
        if headers is None:
            headers = {}
        self.headers = headers

    def __str__(self):
        """Conver this object to string."""
        return "http status: {0}, code:{1} - {2}, reason: {3}".format(
            self.http_status, self.code, self.msg, self.reason
        )


def _make_authorization_headers(client_id, client_secret):
    """Encode authorization headers."""
    auth_header = base64.b64encode((client_id + ":" + client_secret).encode("ascii"))
    return {"Authorization": "Basic %s" % auth_header.decode("ascii")}


class CacheFileHandler:
    """CacheFileHandler class."""

    def __init__(self, cache_path=None):
        """Initialize the CacheFileHandler."""
        if cache_path:
            self.cache_path = cache_path
        else:
            self.cache_path = ".cache"

    def get_cached_token(self):
        """Get a token from cache."""
        token_info = None

        try:
            f = open(self.cache_path)
            token_info_string = f.read()
            f.close()
            token_info = json.loads(token_info_string)

        except IOError as error:
            if error.errno == errno.ENOENT:
                logger.debug("Cache does not exist at: %s", self.cache_path)
            else:
                logger.warning("Couldn't read cache at: %s", self.cache_path)

        return token_info

    def save_token_to_cache(self, token_info):
        """Save a token to cache."""
        try:
            f = open(self.cache_path, "w")
            f.write(json.dumps(token_info))
            f.close()
        except IOError:
            logger.warning("Couldn't write token to cache at: %s", self.cache_path)


class MarietjeAuthBase:
    """Marietje Auth Base class."""

    def __init__(self, requests_session):
        """Initialize Marietje Auth Base."""
        if isinstance(requests_session, requests.Session):
            self._session = requests_session
        else:
            if requests_session:
                self._session = requests.Session()
            else:
                from requests import api

                self._session = api

    @staticmethod
    def is_token_expired(token_info):
        """Check whether a saved token is expired."""
        now = int(time.time())
        return token_info["expires_at"] - now < 60

    def _handle_oauth_error(self, http_error):
        """Handle OAuth errors."""
        response = http_error.response
        try:
            error_payload = response.json()
            error = error_payload.get("error")
            error_description = error_payload.get("error_description")
        except ValueError:
            error = response.text or None
            error_description = None

        raise MarietjeOauthError(
            "error: {0}, error_description: {1}".format(error, error_description),
            error=error,
            error_description=error_description,
        )

    def __del__(self):
        """Make sure the connection (pool) gets closed."""
        if isinstance(self._session, requests.Session):
            self._session.close()


class MarietjeClientCredentials(MarietjeAuthBase):
    """Marietje Client Credentials."""

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        requests_session=True,
        requests_timeout=None,
        cache_path=None,
    ):
        """Initialize Marietje Client Credentials."""
        super(MarietjeClientCredentials, self).__init__(requests_session)
        if not base_url.endswith("/"):
            base_url = base_url + "/"
        self.url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.cache_handler = CacheFileHandler(cache_path=cache_path)
        self.requests_timeout = requests_timeout

    def token_url(self):
        """Get token URL."""
        return self.url + "oauth/token/"

    def get_access_token(self, check_cache=True):
        """Get access token."""
        if check_cache:
            token_info = self.cache_handler.get_cached_token()
            if token_info and not self.is_token_expired(token_info):
                return token_info["access_token"]

        token_info = self._request_access_token()
        token_info = self._add_custom_values_to_token_info(token_info)
        self.cache_handler.save_token_to_cache(token_info)
        return token_info["access_token"]

    def _request_access_token(self):
        """Get client credentials access token."""
        payload = {"grant_type": "client_credentials"}

        headers = _make_authorization_headers(self.client_id, self.client_secret)

        logger.debug("sending POST request to %s with Headers: %s and Body: %r", self.token_url(), headers, payload)

        try:
            response = self._session.post(
                self.token_url(),
                data=payload,
                headers=headers,
                verify=True,
                timeout=self.requests_timeout,
            )
            response.raise_for_status()
            token_info = response.json()
            return token_info
        except requests.exceptions.HTTPError as http_error:
            self._handle_oauth_error(http_error)

    def _add_custom_values_to_token_info(self, token_info):
        """Store some values that aren't directly provided by a Web API response."""
        token_info["expires_at"] = int(time.time()) + token_info["expires_in"]
        return token_info


class Marietje:
    """Marietje class."""

    default_retry_codes = (429, 500, 502, 503, 504)

    def __init__(
        self,
        base_url: str,
        auth=None,
        requests_session=True,
        auth_manager=None,
        requests_timeout=5,
        status_forcelist=None,
        retries=3,
        status_retries=3,
        backoff_factor=0.3,
    ):
        """Initialize Marietje."""
        if not base_url.endswith("/"):
            base_url = base_url + "/"
        self.prefix = base_url
        self._auth = auth
        self._auth_manager = auth_manager
        self.requests_timeout = requests_timeout
        self.status_forcelist = status_forcelist or self.default_retry_codes
        self.backoff_factor = backoff_factor
        self.retries = retries
        self.status_retries = status_retries

        if isinstance(requests_session, requests.Session):
            self._session = requests_session
        else:
            if requests_session:  # Build a new session.
                self._build_session()
            else:  # Use the Requests API module as a "session".
                self._session = requests.api

    @property
    def api_url(self):
        """Get API URL."""
        return self.prefix + "api/v1/"

    @property
    def auth_manager(self):
        """Get the auth manager."""
        return self._auth_manager

    def _build_session(self):
        """Build a request session."""
        self._session = requests.Session()
        retry = urllib3.Retry(
            total=self.retries,
            connect=None,
            read=False,
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
            status=self.status_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )

        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def __del__(self):
        """Make sure the connection (pool) gets closed."""
        if isinstance(self._session, requests.Session):
            self._session.close()

    def _auth_headers(self):
        """Get authentication headers via the auth manager or a fixed Bearer token."""
        if self._auth:
            return {"Authorization": "Bearer {0}".format(self._auth)}
        if not self.auth_manager:
            return {}

        token = self.auth_manager.get_access_token()
        return {"Authorization": "Bearer {0}".format(token)}

    def _internal_call(self, method, url, payload, params):
        """Do an internal request."""
        args = dict(params=params)
        if not url.startswith("http"):
            url = self.api_url + url
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

        logger.debug(
            "Sending %s to %s with Params: %s Headers: %s and Body: %r ",
            method,
            url,
            args.get("params"),
            headers,
            args.get("data"),
        )

        try:
            response = self._session.request(method, url, headers=headers, timeout=self.requests_timeout, **args)

            response.raise_for_status()
            results = response.json()
        except requests.exceptions.HTTPError as http_error:
            response = http_error.response
            try:
                json_response = response.json()
                error = json_response.get("error", {})
                msg = error.get("message")
                reason = error.get("reason")
            except ValueError:
                msg = response.text or None
                reason = None

            logger.error(
                "HTTP Error for %s to %s with Params: %s returned %s due to %s",
                method,
                url,
                args.get("params"),
                response.status_code,
                msg,
            )

            raise MarietjeException(
                response.status_code,
                -1,
                "%s:\n %s" % (response.url, msg),
                reason=reason,
                headers=response.headers,
            )
        except requests.exceptions.RetryError as retry_error:
            request = retry_error.request
            logger.error("Max Retries reached")
            try:
                reason = retry_error.args[0].reason
            except (IndexError, AttributeError):
                reason = None
            raise MarietjeException(429, -1, "%s:\n %s" % (request.path_url, "Max Retries"), reason=reason)
        except ValueError:
            results = None

        logger.debug("RESULTS: %s", results)
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

    def queue_current(self):
        """Get the current queue."""
        return self._get("queues/current/")
