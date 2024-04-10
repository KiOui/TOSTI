# TOSTI

Welcome to the repository of **Tartarus Order System for Take-away Items**, TOSTI for short. 
This application is designed to provide [Tartarus](https://tartarus.science.ru.nl) with an online tool for ordering take-away items.
There are also a lot of other integrated features:

- SAML user authentication (for usage with the Radboud University SSO service)
- A music controller for Spotify and the custom Marietje music system (read-only)
- A QR-code token based identification system
- Transactions / balance tracking for users
- Room reservations
- Borrel reservations (ordering items for an event, and submitting how much were used)
- Synchronization towards a bookkeeping system
- Age verification using [Yivi](https://www.yivi.app)
- A digital lock system for fridges

## Getting started
This project is built using the [Django](https://github.com/django/django) framework. [Poetry](https://python-poetry.org) is used for dependency management.

### Development setup

0. Get [Python](https://www.python.org) 3.11 installed on your system (but 3.8 or higher should work as well, probably). Protip: use [pyenv](https://github.com/pyenv/pyenv) to manage your Python versions.
1. Clone this repository. 
2. Install Poetry by following the steps on [their website](https://python-poetry.org/docs/#installation).
3. Make sure `poetry` uses your your correct base python version: `poetry env use python`. 
4. Run `poetry install` to install all dependencies (into a virtual environment dedicated to this project).
5. Run `poetry shell` to start a shell that uses your virtual environment (or prefix all commands with `poetry run`).
6. Run ```cd website``` to change directories to the ```website``` folder containing the project.
7. Run ```./manage.py migrate``` to initialise the database and run all migrations. 
8. Run ```./manage.py createsuperuser``` to create an administrator that is able to access the backend interface later on. 
9. Run ```./manage.py runserver``` to start the development server locally.

Now your server is setup and running on ```localhost:8000```.
Notice that SAML login will not be used by default on development systems.

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
