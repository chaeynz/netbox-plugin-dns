import django_tables2 as tables

from netbox.tables import NetBoxTable, TagColumn

from netbox_dns.models import RegistrationContact


__all__ = ("RegistrationContactTable",)


class RegistrationContactTable(NetBoxTable):
    contact_id = tables.Column(
        linkify=True,
    )
    tags = TagColumn(
        url_name="plugins:netbox_dns:registrationcontact_list",
    )

    class Meta(NetBoxTable.Meta):
        model = RegistrationContact
        fields = (
            "name",
            "description",
            "organization",
            "street",
            "city",
            "state_province",
            "postal_code",
            "country",
            "phone",
            "phone_ext",
            "fax",
            "fax_ext",
            "email",
        )
        default_columns = ("contact_id", "name", "email")
