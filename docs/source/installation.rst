Installation
============

This project is built using the Django_ framework. Poetry_ is used for dependency management.

Setup
-----

0. Get at least Python_ 3.7 installed on your system.
1. Clone this repository.
2. If ``pip3`` is not installed on your system yet, execute ``apt install python3-pip`` on your system.
3. Also make sure ``python3-dev`` is installed on your system, execute ``apt install python3-dev``.
4. Install Poetry by following the steps on `their website <https://python-poetry.org/docs/#installation>`_. Make sure poetry is added to ``PATH`` before continuing.
5. Make sure ``poetry`` uses your python 3 installation: ``poetry env use python3``.
6. Run ``poetry install`` to install all dependencies.
7. Run ``poetry shell`` to start a shell with the dependencies loaded. This command needs to be ran every time you open a new shell and want to run the development server.
8. Run ``cd website`` to change directories to the ``website`` folder containing the project.
9. Run ``./manage.py migrate`` to initialise the database and run all migrations.
10. Run ``./manage.py createsuperuser`` to create an administrator that is able to access the backend interface later on. The password you set here will not be used as the openid server will be used for identification, be sure to set the super user to your science login name.
11. Run ``./manage.py runserver`` to start the development server locally.

Now your server is setup and running on ``localhost:8000``. The administrator interface can be accessed by going to ``localhost:8000/admin``.

.. _django: https://github.com/django/django
.. _poetry: https://python-poetry.org
.. _python: https://www.python.org