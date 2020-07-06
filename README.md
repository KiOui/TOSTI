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

### Marietje

The `marietje` module is an implementation of the [spotipy](https://spotipy.readthedocs.io) package to create a music control system for venues. A [Spotify](https://spotify.com) account can be linked to a `Venue` to enable a Spotify player to be controlled via a webpage within the `marietje` module. 

Note that the `spotipy` package uses caching for storing Spotify's OAuth2 credentials. This means that a caching folder should be specified in the Django settings file.

#### Setting up a Spotify account

To set up a Spotify account, move to the administration view and add a `SpotifyAccount` object. Then follow these steps:

1. Follow the steps on the page and enter a Client ID and Client Secret. Then press `Authorize` to start the authorization process.
2. Follow the steps on the Spotify website.
3. On the authorization completed view, click on the link to go to the just created `SpotifyAccount` object.
4. There are two last things we need to do, we need to set the playback device id and the `Venue` in which the Spotify account should be displayed. First select a `Venue` from the dropdown list and hit `Save`.
5. Now, start up a Spotify client on some other PC/Smartphone/Tablet, this Spotify client should remain on as it will be the one that is controlled by the `marietje` module. When your Spotify client is not in the list, try refreshing the page. If your client is in the list, select it and hit `Save`.
6. Spotify is now configured and can be controlled via the `marietje` module.