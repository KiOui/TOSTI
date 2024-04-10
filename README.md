# TOSTI

Welcome to the repository of **Tartarus Order System for Take-away Items**, TOSTI for short. This application is designed to provide [Tartarus](https://tartarus.science.ru.nl) with an online tool to order items.
There are also a lot of other integrated features:

- SAML user authentication (for usage with the Radboud University SSO service).
- A music controller for Spotify and the custom Marietje music system (read-only)
- A QR-code token based identification system
- Transactions / balance tracking for users
- Room reservations
- Borrel reservations (ordering items for an event, and submitting how much were used)
- Synchronization towards a bookkeeping system.
- Age verification using [Yivi](https://www.yivi.app).
- A digital lock system for fridges

## Getting started
This project is built using the [Django](https://github.com/django/django) framework. [Poetry](https://python-poetry.org) is used for dependency management.

### Development setup

0. Get at least [Python](https://www.python.org) 3.8.10 installed on your system (production is running on 3.11).
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
TOSTI is deployed using Docker and Docker Compose. The `docker-compose.yml` file is used to define the services that are used in the deployment. The `Dockerfile` is used to define the image that is used for the Django application.

Specifically, TOSTI is running in the [PGO environment](https://github.com/miekg/pgo) of [CNCZ](https://cncz.science.ru.nl/nl/) (the IT department of the Radboud University Faculty of Science). 
This automatically deploys the `docker-compose.yml` file.
To interact with the environment, you should use the [`pgoctl`](https://github.com/miekg/pgo/blob/main/cmd/pgoctl/) client.
This client connects with the PGO API to manage the environment via SSH.
Therefore, your SSH public key must be in the `ssh` directory of this project.

Run (for example) `pgoctl -i ~/.ssh/id_ed25519 -- dockervm02.science.ru.nl:tosti//up` to deploy the application, and `pgoctl -i ~/.ssh/id_ed25519 -- dockervm02.science.ru.nl:tosti//down` to stop the application.
Or run `pgoctl -i ~/.ssh/id_ed25519 -- dockervm02.science.ru.nl:tosti//logs` to see the logs.
Or run `pgoctl -i ~/.ssh/id_ed25519 -- dockervm02.science.ru.nl:tosti//exec web python manage.py sendtestemail` to send a test email.
Notice that `pgoctl` does not (yet) support interactive commands, so you cannot run `manage.py shell` for example.
Also any non-successful commands (with a non-zero exit code) will not be shown and will not show their output.
Finally, you must be connected with the CNCZ VPN to use `pgoctl`.

Important notices:
- Via `/admin-login`, it is possible to bypass SAML login (for example for first installation when SAML has not yet been set up).
