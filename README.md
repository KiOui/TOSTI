# TOSTI

Welcome to the repository of Tartarus Order System for Take-away Items, TOSTI for short. This application is designed to provide [Tartarus](https://tartarus.science.ru.nl) with an online tool to order items.

The current system features the following:

- A custom user model that makes it able to authenticate via the [science openid server](https://openid.science.ru.nl).
- A really nice model structure where new venues, products and staff users can be easily added.
- A beautiful minimal interface to order your products online

## Getting started

This project is built using the [Django](https://github.com/django/django) framework. [Poetry](https://python-poetry.org) is used for dependency management.

### Setup

0. Get at least [Python](https://www.python.org) 3.7 installed on your system.
1. Clone this repository.
2. If ```pip3``` is not installed on your system yet, execute ```apt install python3-pip``` on your system.
3. Also make sure ```python3-dev``` is installed on your system, execute ```apt install python3-dev```.
4. Install Poetry by following the steps on [their website](https://python-poetry.org/docs/#installation). Make sure poetry is added to ```PATH``` before continuing.
5. Make sure `poetry` uses your python 3 installation: `poetry env use python3`.
6. Run `poetry install` to install all dependencies.
7. Run `poetry shell` to start a shell with the dependencies loaded. This command needs to be ran every time you open a new shell and want to run the development server.
8. Run ```cd website``` to change directories to the ```website``` folder containing the project.
9. Run ```./manage.py migrate``` to initialise the database and run all migrations.
10. Run ```./manage.py createsuperuser``` to create an administrator that is able to access the backend interface later on. The password you set here will not be used as the openid server will be used for identification, be sure to set the super user to your science login name.
11. Run ```./manage.py runserver``` to start the development server locally.

Now your server is setup and running on ```localhost:8000```. The administrator interface can be accessed by going to ```localhost:8000/admin```.

## Module explanations

This section will go over the modules in TOSTI and explain design decisions and basic funtionality.

### Venues

The venues module provides a model `Venue` for differentiating between venues. This way, users can interact with multiple venues from the same website.

### Orders

There are two important functionalities of the orders module. The first being the ability to create, manage and start shifts with different users. The second being the ability for users to place orders in shifts.

#### Products

Products are items users can order in shifts.

#### Shifts

A user with the authorization of creating shifts can create a `Shift` for a specific `Venue`. There can only be one shift at a specific time per venue. Shifts represent time windows in which users can place and pick up orders. 

Users can only place orders in active shifts, a shift is active if an authorized user has set a shift to active and if the current time is within the time window of the shift.

A maximum amount of orders can be set on a per shift and per user basis.

#### Orders

Orders can be placed in active shifts. A user can place an order by specifying the ``Product`` he or she wants to order.

### Users

The custom `users` module enables TOSTI to authenticate users via OpenID. Currently, [OpenID version 1.1](https://openid.net/specs/openid-authentication-1_1.html#mode_associate) is supported by the `users` module. An OpenID host can be set in the settings file by specifying the following variable:

- `OPENID_SERVER_ENDPOINT`: the server endpoint fot the OpenID verification

Additionally, the following variables can be set in settings to change the behaviour of the OpenID implementation:

- `OPENID_RETURN_URL`: where the user should be taken when coming from the OpenID server (should be set to a view name)
- `OPENID_USERNAME_PREFIX`: a prefix to prepend to the username users enter when starting authentication
- `OPENID_USERNAME_POSTFIX`: a postfix to append to the username users enter when starting authentication

### Thaliedje

This module is used to connect a Spotify player to venues. A SpotifyAccount object can be configured and connected to a venue. This enables users of TOSTI to control and listen to music from Spotify. The main features of the Thaliedje module are:

- Connecting a Spotify account to TOSTI
- Showing the currently playing song
- Controlling the queue and controls for play/pausing the song and skipping/reverting a track

The Thaliedje module makes use of the [Spotify API](https://developer.spotify.com) via the [spotipy library](https://spotipy.readthedocs.io/en/2.12.0/). There are three stages in configuring Thaliedje for playback controls:

1. Adding a Spotify account to TOSTI

In order to add a Spotify account to TOSTI, head over to the administrator view and add a `Spotify Settings` object to the database. You will be automatically redirected to a page where you need to enter a public and private Spotify API key which can be created on the [Spotify API dashboard](https://developer.spotify.com/dashboard/applications). Follow the instructions on the page and continue to the next step if everything succeeded.

Note that the spotipy library makes use of its own caching system to cache the Spotify OAUTH2 tokens. The directory where these cache files are stored can be configured by setting the `SPOTIFY_CACHE_PATH` in the Django settings file. Only the Spotify API client id and client secret are stored in the Django database, the other identifiers and keys used in the OAUTH2 protocol are handled by spotipy and are thus stored in the spotipy cache files.

2. Configuring a Spotify account

A Spotify account can be configured after setting it up. Two things need to be changed before a venue is shown with a music player on the Thaliedje overview page:

- Set a venue
- Set a playback device

Setting a venue is easy, just select the venue from the dropdown list and it will be connected to the Spotify account you are configuring. Setting a playback device is a little more difficult as now is the time where you need to start up a Spotify client on a computer system connected to the internet. Note that after setting a playback device, the device must stay on and the Spotify client must remain open, otherwise the pages corresponding to the Spotify account will throw a server error (500) as the playback device can not be found. If the playback device is not displayed within the list, refresh the configuration page and try again. After setting a playback device and venue, a spotify player is shown at `/thaliedje/index`.

3. Using the playback functions

If everything went well, a Spotify player is displayed on the `/thaliedje/index` page. Administrators are able to play/pause and skip or revert songs, normal users are not. If you open the Spotify player, a search view is displayed and the recent items added to the queue. The search view can be used to search tracks on Spotify. The queue displays only tracks added via Thaliedje, as there is currently no way to request the queue from a Spotify playback device.

### Tantalus

The `tantalus` module is used to synchronize Orders to a [Tantalus](https://github.com/thijsmie/tantalus) instance. The following (Docker environment) settings must be set in order for synchronization to work:

- `TANTALUS_ENDPOINT_URL`: the endpoint of the Tantalus client, usually ending with `/poscl/`
- `TANTALUS_USERNAME`: the username of the account that is used to log into Tantalus
- `TANTALUS_PASSWORD`: the password of the account that is used to log into Tantalus

Order registration will happen once a `Shift` is made finalized for all `Product` objects with a registered `TantalusProduct` object and if the `OrderVenue` of the `Shift` has a registered `TantalusOrderVenue`  (and thus Tantalus endpoint).


## Deploying
0. Clone this repo in `/www/tosti/live/repo` (on the science filesystem)
1. Create python 3.8 venv with `/www/tosti/live/repo/env`
2. Install the dependencies in requirements.txt
3. Create `/www/tosti/live/repo/website/tosti/settings/production.py` and `/www/tosti/live/repo/website/tosti/settings/management.py` based on the `.example` files (set secret key and passwords).
4. `touch RELOAD` to trigger uWSGI to reload the django application
5. Do not forget to create a `/media/` and `/spotifycache/` folder in `/www/tosti/live/writable/`, and run `manage.py collectstatic` to build the static folder (in `/www/tosti/live/repo/static/`). The webserver itself does not have write-permissions to do this.

Note that the webserver runs on a different machine then how you access it via lilo. The file system is mounted differently, so using relative paths is required. Also, for example, the password to access the database is different from lilo (via `manage.py`) the on real production. This requires the different `settings` files. Specifically, `wsgi.py` (ran by the webserver) needs a different settings file then `manage.py` (ran on lilo).

To run management commands on production, first activate the python env with `source env/bin/activate` and then set an env variable to run `manage.py` with the correct settings: `export DJANGO_SETTINGS_MODULE=tosti.settings.management`

### SAML configuration
To login, we use SAML. This needs to be configured. The SAML metadata for the CNCZ SAML IdP right now:

```xml
<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" entityID="signon.science.ru.nl/saml-ru">
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:KeyDescriptor use="signing">
            <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                <ds:X509Data>
                    <ds:X509Certificate>MIIETzCCAzegAwIBAgIJAKwffKBlFTjcMA0GCSqGSIb3DQEBBQUAMIG9MQswCQYDVQQGEwJOTDETMBEGA1UECAwKR2VsZGVybGFuZDERMA8GA1UEBwwITmlqbWVnZW4xLzAtBgNVBAoMJlJhZGJvdWQgVW5pdmVyc2l0eSwgRmFjdWx0eSBvZiBTY2llbmNlMQ0wCwYDVQQLDARDTkNaMR0wGwYDVQQDDBRzaWdub24uc2NpZW5jZS5ydS5ubDEnMCUGCSqGSIb3DQEJARYYcG9zdG1hc3RlckBzY2llbmNlLnJ1Lm5sMB4XDTEzMTAxNzE4MzYxMVoXDTMzMTAxMjE4MzYxMVowgb0xCzAJBgNVBAYTAk5MMRMwEQYDVQQIDApHZWxkZXJsYW5kMREwDwYDVQQHDAhOaWptZWdlbjEvMC0GA1UECgwmUmFkYm91ZCBVbml2ZXJzaXR5LCBGYWN1bHR5IG9mIFNjaWVuY2UxDTALBgNVBAsMBENOQ1oxHTAbBgNVBAMMFHNpZ25vbi5zY2llbmNlLnJ1Lm5sMScwJQYJKoZIhvcNAQkBFhhwb3N0bWFzdGVyQHNjaWVuY2UucnUubmwwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDPOH0c2f3n4XluMoPfje/MiaoXhCri+amfOtnafdmYGbyGuwF72F0uq6MvNX3OdtBbDGmnFpfQYspfS7jNjFUvkLsnIMGPY4p+5lDD675cKn9CnwfsA1cppZl2Zc09Zf3BLKelKNzYWtAvY7sNX9e4NntlcObgW1yqZCg9JC8X8CY1xKMwkbGEl4Ltxc636+mOiZsKduD7kcL9Hf1akT4wX3WGhXsQbifbVrBIoBCV4Rom8n4YDrxdqi7+bRx1wNhi6Y0tALYqxdAJ/J3wLm6tzFcNketIKUTN4r0gq+mAQSo0Lcwt/GpdlFqD6EoEFSlcqAqxfeWK4PWLeDyOQD4FAgMBAAGjUDBOMB0GA1UdDgQWBBT/3wfM9BDMslqpaNXoJlmv4vn9rTAfBgNVHSMEGDAWgBT/3wfM9BDMslqpaNXoJlmv4vn9rTAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4IBAQBlcARvzuYwIKmnF4fXbl7yAmAfbELoFzbrdZYL+ZWePjPAgw/gDrjpWC8JcVdprt3BPHLj1tu+oWexOVGxVUGxAZyRm/7IvADz5N7BCSwG4zeqDcjkVOdKhlEjJVXquENpU1VnrwqFahh1Hdtryyjp27nNQtkgUKxbV47nO+cWYIVruia9SFwkOczWr+c8IE4lYjgycD6nKRQJzCeUpVfa/ROtHZJ4XxQUMPNE2OmT3gGygbu2QKOm8jiC1w9TDOlAZcDx8zF3hwFYh/gWd/x4CC0VZEEwCb1meWezr5X6jXvVjVduH32yfkld2ZvpFzjD5DPicZTRT/jLCXi++0+s</ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </md:KeyDescriptor>
        <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://r2.signon.science.ru.nl/saml-ru/saml2/idp/SingleLogoutService.php"/>
        <md:NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</md:NameIDFormat>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://r2.signon.science.ru.nl/saml-ru/saml2/idp/SSOService.php"/>
    </md:IDPSSODescriptor>
</md:EntityDescriptor>
```

For our `url_params` we use: `{"idp_slug": "science_puc"}`, base url `https://tosti.science.ru.nl` and entity id `tosti.science.ru.nl` (!).

The attributes returned are: `uid`, which is the `NameID` and should be mapped to the `username` field. The `displayName` is expected to be mapped to `first_name` initially (and not updated afterwards).

Moreover, we use the following settings:

- User default values: `is_staff` is `True` so every user can actually see the (empty) admin page.
- `NameID is case sensitive` is `False`
- `Create users that do not already exist` is `True`
- `Associate existing users with this IdP by username` is `True` (this is a vulnerability for username spoofing but with only 1 IdP this is no problem)
- `Respect IdP session expiration` is `True` (!)
- `Logout triggers SLO` is `True` as well

