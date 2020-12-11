from django.db.models import ProtectedError
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ParseError, ValidationError, NotFound
from rest_framework.views import APIView
from rest_framework import status

from orders.api.serializers.orders import OrderSerializer, ShiftSerializer, ProductSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product
from orders.services import Cart, place_orders, increase_shift_time, increase_shift_capacity, add_order


class OrderView(APIView):
    """APIView to order all cart items."""

    def _extract_cart(self):
        """
        Extract the cart items from the POST data.

        :return: a Cart object with the cart items as specified in the cart in the POST data. Raises a ValidationError
        when there is not cart in the POST data. Raises a ParseError when the cart can not be parsed.
        """
        cart_as_id_list = self.request.data.get("cart", None)
        if cart_as_id_list is None:
            raise ValidationError

        try:
            return Cart.from_list(cart_as_id_list)
        except ValueError:
            raise ParseError

    def get_object(self):
        """
        Get the Shift the user wants to add the orders to.

        :return: a Shift object
        """
        return self.kwargs.get("shift")

    def post(self, request, **kwargs):
        """
        API endpoint for creating multiple orders in one go (handling of a cart).

        A "cart" POST parameter must be specified including the ID's of the Products the user wants to order.
        Permission required: can_order_in_venue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a 201 response code if all orders in the cart were successfully processed. Raises a ValidationError
        if some Orders in the cart can not be processed. Returns a 400 response code if the cart could not be read or is
        not present in the POST data, raises a PermissionDenied error when the user does not have permission
        """
        shift = self.get_object()
        if not self.request.user.has_perm("orders.can_order_in_venue", shift.venue):
            raise PermissionDenied

        try:
            cart = self._extract_cart()
        except ValidationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            place_orders(cart.get_item_list(), request.user, shift)
        except OrderException as e:
            raise ValidationError(e.__str__())
        return Response(status=status.HTTP_201_CREATED)


class OrderViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """
    API endpoint for Order model.

    Contains the following methods:
    - Create
    - List
    - Retrieve
    - Update
    """

    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_permissions(self):
        # TODO: Implement get_permissions instead of permissions in each method
        """
        if self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        """
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        API endpoint for creating a single Order.

        A 'shift' POST parameter must be present indicating the Shift the order must be added to.
        Permission required: can_order_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return:
        """
        shift_id = request.data.get('shift', None)
        if shift_id is not None:
            try:
                shift = Shift.objects.get(id=shift_id)
            except Shift.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.user.has_perm("orders.can_order_in_venue", shift.venue):
            pass
            # TODO: Use serializer create method?

    def list(self, request, *args, **kwargs):
        """
        API endpoint for listing all Orders.

        Optionally a 'shift' parameter can be specified indicating the Shift to list the Orders for.
        Permission required: None
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method
        """
        shift_id = request.data.get('shift', None)
        if shift_id:
            self.queryset = Order.objects.filter(shift=shift_id)

        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        API endpoint for updating an Order.

        Permission required: can_manage_shift_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied
        """
        order = self.get_object()
        if self.request.user.has_perm("orders.can_manage_shift_in_venue", order.shift.venue):
            return super().update(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ShiftViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """
    API endpoint for Shift model.

    Contains the following methods:
    - Create
    - List
    - Retrieve
    - Update
    """

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()

    def create(self, request, *args, **kwargs):
        """
        API endpoint for creating a Shift.

        Permission required: can_manage_shift_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied when 'venue' POST data is None or when user does not have permission
        in indicated venue
        """
        venue = request.data.get('venue', None)
        if venue is not None and self.request.user.has_perm("orders.can_manage_shift_in_venue", venue):
            return super().create(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def update(self, request, *args, **kwargs):
        """
        API endpoint for updating a Shift.

        Permission required: can_manage_shift_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied
        """
        shift = self.get_object()
        if self.request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
            return super().update(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def list(self, request, *args, **kwargs):
        """
        API endpoint for listing Shift objects.

        Optionally an 'active' POST parameter can be set indicating whether or not to only show active Shifts.
        Permission required: None
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: a response with Shift objects serialized
        """
        active = request.query_params.get("active", None)
        if active is not None:
            active = active == "true"
            queryset = [x for x in self.queryset if x.is_active == active]
        else:
            queryset = self.queryset
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        API endpoint for retrieving a Shift object.

        Permission required: None
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method
        """
        return super().retrieve(request, *args, **kwargs)


class ProductViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    API endpoint for Product model.

    Contains the following methods:
    - Create
    - List
    - Retrieve
    - Update
    - Destroy
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def create(self, request, *args, **kwargs):
        """
        API endpoint for creating a Product.

        Permission required: is_staff
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied
        """
        if request.user.is_staff:
            super().create(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def update(self, request, *args, **kwargs):
        """
        API endpoint for updating a Product.

        Permission required: is_staff
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied
        """
        if request.user.is_staff:
            super().create(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def destroy(self, request, *args, **kwargs):
        """
        API endpoint for destroying a Product.

        Permission required: is_staff
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method when succeeded, a 403 response indicating the Product could not be deleted because there
        are still Orders that depend on it or PermissionDenied
        """
        if request.user.is_staff:
            try:
                return super().destroy(request, *args, **kwargs)
            except ProtectedError as e:
                return Response(data={"detail": "Cannot delete some instances of model 'Product' because some orders still use them.", "objects": [x.pk for x in e.protected_objects]}, status=status.HTTP_403_FORBIDDEN)
        else:
            raise PermissionDenied

    def list(self, request, *args, **kwargs):
        """
        API endpoint for listing Products.

        Permission required: None
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method
        """
        super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        API endpoint for retrieving a Product.

        Permission required: None
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method
        """
        super().retrieve(request, *args, **kwargs)


@api_view(['POST'])
def shift_add_time(request, **kwargs):
    """
    API endpoint for adding an amount of minutes to the end of a Shift.

    Optionally a "minutes" POST parameter can be set indicating with how many minutes the time should be extended.
    Permission required: can_manage_shift_in_venue
    :param request: the request
    :param kwargs: keyword arguments
    :return: a response with a status code of 204 or a PermissionDenied error
    """
    shift = kwargs.get("shift")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        time_minutes = request.data.get("minutes", 5)
        increase_shift_time(shift, time_minutes)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        raise PermissionDenied


@api_view(['POST'])
def shift_add_capacity(request, **kwargs):
    """
    API endpoint for adding capacity to a Shift.

    Optionally a "capacity" POST parameter can be set indicating how many capacity should be added.
    Permission required: can_manage_shift_in_venue
    :param request: the request
    :param kwargs: keyword arguments
    :return: a response with a status code of 204 or a PermissionDenied error
    """
    shift = kwargs.get("shift")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        time_minutes = request.data.get("capacity", 5)
        increase_shift_capacity(shift, time_minutes)
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        raise PermissionDenied


@api_view(['POST'])
def shift_scanner(request, **kwargs):
    """
    API endpoint for adding a scanned order to a Shift.

    A "barcode" POST parameter should be specified indicating the barcode of the product to add.
    Permission required: can_manage_shift_in_venue
    :param request: the request
    :param kwargs: keyword arguments
    :return: a response with a status code of 404 when the product is not found, a response with a status code of 204
    when the product is found and successfully ordered or a PermissionDenied error
    """
    shift = kwargs.get("shift")
    barcode = request.data.get("barcode", None)
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        try:
            product = Product.objects.get(barcode=barcode, available=True, available_at=shift.venue)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        Order.objects.create(shift=shift, product=product, type=Order.TYPE_SCANNED, paid=True, ready=True)
        return Response(status=status.HTTP_201_CREATED)
    else:
        raise PermissionDenied
