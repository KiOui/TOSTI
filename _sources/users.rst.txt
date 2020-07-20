Users package
=================

.. automodule:: users
   :members:
   :undoc-members:
   :show-inheritance:

OpenID implementation
---------------------
The user module lets Django use the `Science OpenID server`_ for authentication. The `Science OpenID server`_ uses
`OpenID version 1.1`_. The ``OpenIDVerifier`` object in ``users/services`` handles all OpenID verification.

User models
-----------
This module does not create a custom Django user model but rather uses the common `auth.User` model. In addition,
the module contains a `GroupSettings` model, related to the `auth.Group` model, to define special properties for
certain `auth.Group`'s.

Submodules
----------

users.admin module
----------------------

.. automodule:: users.admin
   :members:
   :undoc-members:
   :show-inheritance:

users.apps module
---------------------

.. automodule:: users.apps
   :members:
   :undoc-members:
   :show-inheritance:

users.forms module
----------------------

.. automodule:: users.forms
   :members:
   :undoc-members:
   :show-inheritance:

users.models module
-----------------------

.. automodule:: users.models
   :members:
   :undoc-members:
   :show-inheritance:

users.urls module
---------------------

.. automodule:: users.urls
   :members:
   :undoc-members:
   :show-inheritance:

users.views module
----------------------

.. automodule:: users.views
   :members:
   :undoc-members:
   :show-inheritance:

.. _science openid server: https://openid.science.ru.nl
.. _openid version 1.1: https://openid.net/specs/openid-authentication-1_1.html#mode_associate