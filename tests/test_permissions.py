# -*- coding: utf-8 -*-
"""
Tests for the taxonomy permissions.
"""
from collections import namedtuple

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.test import TestCase

from taxonomy.api.permissions import IsOwner

User = get_user_model()  # pylint: disable=invalid-name
USER_PASSWORD = 'QWERTY'


class PermissionsTestMixin:
    """
    Test mixin for permissions.
    """
    def get_request(self, user=None, data=None):
        """
        Creates a Request object and associates with the user passed.
        """
        request = APIRequestFactory().post('/', data)

        if user:
            force_authenticate(request, user=user)

        return Request(request, parsers=(JSONParser(),))


class IsOwnerTests(PermissionsTestMixin, TestCase):
    """
    Tests for ``IsOwner`` permission class.
    """
    permissions_class = IsOwner()
    dummy_class = namedtuple("DummyClass", "username")

    def setUp(self) -> None:
        super(IsOwnerTests, self).setUp()
        self.user = User.objects.create(username="rocky")
        self.user.set_password(USER_PASSWORD)
        self.user.save()

    def test_obj_owner_has_permission(self):
        """
        Verify that owner of object has access to the object.
        """
        request = self.get_request(user=self.user)
        dummy_obj = self.dummy_class(username="rocky")
        self.assertTrue(self.permissions_class.has_object_permission(request, None, dummy_obj))

    def test_not_obj_owner_permission(self):
        """
        Verify that users except owner cannot access the object.
        """
        request = self.get_request(user=self.user)
        dummy_obj = self.dummy_class(username="rocky-bad")
        self.assertFalse(self.permissions_class.has_object_permission(request, None, dummy_obj))
