from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import connection, models

from warden.exceptions import ActionNotAllowed

DB_USER_CREATION_SQL = "CREATE USER %s WITH ENCRYPTED PASSWORD '%s'"


class DatabaseUser(models.Model):
    """
    This model is responsible for creating and tracking Database users
    """

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    db_username = models.CharField("Database username", max_length=63)
    password = models.CharField("Password", max_length=128)

    def save(self, *args, **kwargs):
        raw_password = self.password
        self.password = make_password(self.password)
        created = not self.id

        super(DatabaseUser, self).save(*args, **kwargs)
        # Create database user
        if created or kwargs.get("force_db_creation"):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE USER {self.db_username} WITH ENCRYPTED PASSWORD %s",
                    [raw_password],
                )


def database_user_post_delete(
    sender: DatabaseUser, instance: DatabaseUser, **kwargs
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"DROP USER IF EXISTS {instance.db_username}")


def database_user_pre_save(
    sender: DatabaseUser, instance: DatabaseUser, **kwargs
) -> None:
    try:
        obj = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        pass
    else:
        if obj.db_username != instance.db_username or obj.password != instance.password:
            raise ActionNotAllowed(
                "Updates are currently not supported for database users."
            )


models.signals.post_delete.connect(
    database_user_post_delete,
    sender=DatabaseUser,
    dispatch_uid="post_delete_database_user",
)
models.signals.pre_save.connect(
    database_user_pre_save, sender=DatabaseUser, dispatch_uid="pre_save_database_user"
)
