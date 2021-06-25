from django.db import connection, models

from warden.exceptions import ActionNotAllowed

PRIVILEGE_GRANTING_SQL = "GRANT %s ON %s TO %s"


class DatabasePermission(models.Model):
    """
    Model representing a privilege granted to a database user
    """

    INSERT = "I"
    SELECT = "S"
    UPDATE = "U"
    DELETE = "D"
    TRUNCATE = "T"
    REFERENCES = "R"
    PRIVILEGES = (
        (INSERT, "INSERT"),
        (SELECT, "SELECT"),
        (UPDATE, "UPDATE"),
        (DELETE, "DELETE"),
        (TRUNCATE, "TRUNCATE"),
        (REFERENCES, "REFERENCES"),
    )
    table_name = models.CharField("Table name", max_length=63, null=False, blank=False)
    privilege = models.CharField(max_length=1, choices=PRIVILEGES, default=SELECT)
    user = models.ForeignKey("warden.DatabaseUser", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["table_name", "privilege", "user"]


def permission_post_save(
    sender: DatabasePermission,
    instance: DatabasePermission,
    created: bool = False,
    **kwargs,
) -> None:
    if created:
        with connection.cursor() as cursor:
            # Grant user privileges on the database table
            cursor.execute(
                f"GRANT {instance.get_privilege_display()} ON {instance.table_name} TO {instance.user.db_username}"
            )


def permission_post_delete(
    sender: DatabasePermission, instance: DatabasePermission, **kwargs
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"REVOKE {instance.get_privilege_display()} ON TABLE {instance.table_name} FROM {instance.user.db_username}"
        )


def permission_pre_save(
    sender: DatabasePermission, instance: DatabasePermission, **kwargs
):
    try:
        obj = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        pass
    else:
        if (
            obj.table_name != instance.table_name
            or obj.privilege != instance.privilege
            or obj.user != instance.user
        ):
            raise ActionNotAllowed(
                "Updates are currently not supported for database permissions."
            )


models.signals.post_save.connect(
    permission_post_save,
    sender=DatabasePermission,
    dispatch_uid="post_save_db_permission",
)
models.signals.post_delete.connect(
    permission_post_delete,
    sender=DatabasePermission,
    dispatch_uid="post_delete_db_permission",
)
models.signals.pre_save.connect(
    permission_pre_save,
    sender=DatabasePermission,
    dispatch_uid="pre_save_db_permission",
)
