from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase

from warden.exceptions import ActionNotAllowed
from warden.models import DatabasePermission, DatabaseUser


class TestModels(TestCase):
    def _create_database_user(self, user_data: dict = {}):
        user = User.objects.create(
            username="bob", password="bob", email="bob@testing.bob"
        )
        user.refresh_from_db()
        data = {"db_username": "bob", "user": user, "password": "bob"}
        data.update(user_data)
        db_user = DatabaseUser.objects.create(**data)
        db_user.refresh_from_db()
        return db_user

    def test_user_db_permissions_granted(self):
        """
        Test that the creation of Database permissions actually grants a user
        permissions on the database table
        """
        sql = "SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_name='warden_databaseuser' AND grantee=%s"
        user = self._create_database_user()
        # Ensure permission is not present
        with connection.cursor() as cursor:
            cursor.execute(sql, [user.db_username])
            self.assertEqual(cursor.fetchall(), [])

        perm = DatabasePermission.objects.create(
            table_name="warden_databaseuser",
            privilege=DatabasePermission.SELECT,
            user=user,
        )
        with connection.cursor() as cursor:
            cursor.execute(sql, [user.db_username])
            self.assertEqual(cursor.fetchall(), [(user.db_username, "SELECT")])

        # Database permission is deleted on object deletion
        perm.delete()
        with connection.cursor() as cursor:
            cursor.execute(sql, [user.db_username])
            self.assertEqual(cursor.fetchall(), [])

    def test_user_lifecycle_on_db_level(self):
        """
        Test that the creation of a Database user actually creates
        a database user and deletes the user if the Database user object is
        deleted
        """
        sql = "SELECT usename FROM pg_shadow WHERE usename='bob'"
        # Ensure rolename is not present
        with connection.cursor() as cursor:
            cursor.execute(sql)
            self.assertIsNone(cursor.fetchone())

        # Create database user object
        user = self._create_database_user()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            self.assertEqual(cursor.fetchone(), ("bob",))

        # Database user deleted on object deletion
        user.delete()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            self.assertIsNone(cursor.fetchone())

    def test_user_updates_not_allowed(self):
        """
        Test that updates are currently not allowed on the Database user
        """
        user = self._create_database_user()
        user.db_username = "changed"
        with self.assertRaises(ActionNotAllowed):
            user.save()

    def test_permission_updates_not_allowed(self):
        """
        Test that updates of permission objects are not allowed
        """
        user = self._create_database_user()
        perm = DatabasePermission.objects.create(
            table_name="warden_databaseuser",
            privilege=DatabasePermission.SELECT,
            user=user,
        )

        with self.assertRaises(ActionNotAllowed):
            perm.privilege = perm.INSERT
            perm.save()
