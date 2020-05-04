# TOSTI

Welcome to the repository of Tartarus Order System for Take-away Items, TOSTI for short. This application is designed to provide [Tartarus](tartarus.science.ru.nl) with an online tool to order items.

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
