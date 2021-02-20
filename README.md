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

### Docker
For running this application with a docker, a docker image of the latest build is provided on [this page](https://hub.docker.com/repository/docker/larsvanrhijn/tosti). You can also build your own docker image by executing ```docker build .``` in the main directory. An example docker-compose file is added as ```docker-compose.yml.example```.

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
