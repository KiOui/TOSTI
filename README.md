# TOSTI

Welcome to the repository of **Tartarus Order System for Take-away Items**, TOSTI for short. This application is designed to provide [Tartarus](https://tartarus.science.ru.nl) with an online tool to order items.

The current system features the following:

- SAML user authentication (for usage with the Radboud University SSO service).
- A really nice model structure where new venues, products and staff users can be easily added.
- A beautiful minimal interface to order your products online.
- A system for managing Spotify clients.

## Getting started
This project is built using the [Django](https://github.com/django/django) framework. [Poetry](https://python-poetry.org) is used for dependency management.

### Development setup

0. Get at least [Python](https://www.python.org) 3.8.10 installed on your system.
1. Clone this repository.
2. If ```pip3``` is not installed on your system yet, execute ```apt install python3-pip``` on your system.
3. Also make sure ```python3-dev``` is installed on your system, execute ```apt install python3-dev```. On some systems `xmlsec` or `libxmlsec1-dev` should also be installed at the OS level.
4. Install Poetry by following the steps on [their website](https://python-poetry.org/docs/#installation). Make sure poetry is added to ```PATH``` before continuing.
5. Make sure `poetry` uses your python 3 installation: `poetry env use python3`.
6. Run `poetry install` to install all dependencies.
7. Run `poetry shell` to start a shell with the dependencies loaded. This command needs to be run every time you open a new shell and want to run the development server.
8. Run ```cd website``` to change directories to the ```website``` folder containing the project.
9. Run ```./manage.py migrate``` to initialise the database and run all migrations.
10. Run ```./manage.py createsuperuser``` to create an administrator that is able to access the backend interface later on. The password you set here will not be used as the openid server will be used for identification, be sure to set the super user to your science login name.
11. Run ```./manage.py runserver``` to start the development server locally.

Now your server is setup and running on ```localhost:8000```. The administrator interface can be accessed by going to ```localhost:8000/admin```.

SAML login will not be used by default on development systems.

For deployment situations, use `poetry export -f requirements.txt --output requirements.txt` to export the requirements to a `requirements.txt` file.


## Module features
### Venues
- Venue model, so functionalities can be linked to different venues.
- Reservations for venues

### Associations
- Association model

### Users
- User model to override certain methods
- Features for semi-automated user management
- RU SAML specific fixes

### Orders
There are two important functionalities of the orders module. The first being the ability to create, manage and start shifts with different users. The second being the ability for users to place orders in shifts.

#### Products
- Products are items users can order in shifts
- Different kinds of products can be added
- Limitations on ordering products

#### Shifts
- A user with the authorization of creating shifts can create a shift for a specific `venue
- There can only be one shift at a specific time per venue
- Shifts represent time windows in which users can place and pick up orders 
- Limitations on orders in the shift
- Finalizing shifts 'locks' the results

#### Orders
- The order of a product by a user
- Orders can be placed in active shifts
- Placing multiple orders (OrderCart) is only support at the interface level
- Orders can be scanned (for products with a bar code) or ordered. Scanned orders are automatically delivered and paid.

### Thaliedje
The Thaliedje module makes use of the [Spotify API](https://developer.spotify.com) via the [spotipy library](https://spotipy.readthedocs.io/en/2.12.0/).

- Connecting a Spotify account to the system, linking it to a venue
- Showing the currently playing song
- Controlling the queue and controls for play/pausing the song and skipping/reverting a track
- Different permissions

### Tantalus
The `tantalus` module is used to synchronize Orders to a [Tantalus](https://github.com/thijsmie/tantalus) instance. The following (Docker environment) settings must be set in order for synchronization to work:

- `TANTALUS_ENDPOINT_URL`: the endpoint of the Tantalus client, usually ending with `/poscl/`
- `TANTALUS_USERNAME`: the username of the account that is used to log into Tantalus
- `TANTALUS_PASSWORD`: the password of the account that is used to log into Tantalus

Order registration will happen once a `Shift` is made finalized for all `Product` objects with a registered `TantalusProduct` object and if the `OrderVenue` of the `Shift` has a registered `TantalusOrderVenue`  (and thus Tantalus endpoint).

## Deploying
0. Clone this repo in `/www/tosti/live/repo` (on the science filesystem)
1. Create python 3.8 venv with `/www/tosti/live/repo/env`
2. Install the dependencies. Use `poetry export -f requirements.txt --output requirements.txt` to export the requirements to a `requirements.txt` file.
3. Create `/www/tosti/live/repo/website/tosti/settings/production.py` and `/www/tosti/live/repo/website/tosti/settings/management.py` based on the `.example` files (set secret key and passwords).
4. Run the `deploy.sh` script. This script can be run to update, too.

Important notices:
- The science filesystem (accessed via lilo) is mounted in a different way then on lilo. Make sure to use relative paths.
- The database credentials for differ for lilo or the webserver. Therefore, management commands from lilo must be run with `tosti.settings.management` (which is done automatically by `manage.py`).
- To run management commands on production, first activate the python env with `source env/bin/activate`.
- Note that the webserver does not have write permissions, except for the `writable/` folder. `manage.py collectstatic` must therefore be run explicitly.
- Via `/admin-login`, it is possible to bypass SAML login (for example for first installation when SAML has not yet been set up).
