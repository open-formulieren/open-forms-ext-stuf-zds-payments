import logging
from typing import Any

from django.utils.translation import gettext_lazy as _

from openforms.registrations.contrib.stuf_zds.plugin import (
    StufZDSRegistration,
    ZaakOptionsSerializer,
)
from openforms.registrations.contrib.stuf_zds.utils import flatten_data
from openforms.registrations.registry import register
from openforms.submissions.models import Submission
from openforms.variables.service import get_static_variables
from rest_framework import serializers
from stuf.stuf_zds.client import ZaakOptions

from .client import get_client
from .registration_variables import register as variables_registry

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "stuf-zds-create-zaak:ext-utrecht"


def default_payment_status_update_mapping() -> list[dict[str, str]]:
    return [
        {"form_variable": "payment_completed", "stuf_name": "payment_completed"},
        {"form_variable": "payment_amount", "stuf_name": "payment_amount"},
        {
            "form_variable": "payment_public_order_ids",
            "stuf_name": "payment_public_order_ids",
        },
        {"form_variable": "provider_payment_ids", "stuf_name": "provider_payment_ids"},
    ]


def prepare_value(value: Any):
    match value:
        case bool():
            return "true" if value else "false"
        case float():
            return str(value)
        case _:
            return value


class MappingSerializer(serializers.Serializer):
    form_variable = serializers.CharField(
        help_text=_("The name of the form variable to be mapped")
    )
    stuf_name = serializers.CharField(
        help_text=_("The name in StUF-ZDS to which the form variable should be mapped"),
        label=_("StUF-ZDS name"),
    )


class ZaakPaymentOptionsSerializer(ZaakOptionsSerializer):
    payment_status_update_mapping = MappingSerializer(
        many=True,
        label=_("payment status update variable mapping"),
        help_text=_(
            "This mapping is used to map the variable keys to keys used in the XML "
            "that is sent to StUF-ZDS. Those keys and the values belonging to them in "
            "the submission data are included in extraElementen."
        ),
        required=False,
    )

    @classmethod
    def display_as_jsonschema(cls):
        data = super().display_as_jsonschema()
        # Workaround because drf_jsonschema_serializer does not pick up defaults
        data["properties"]["payment_status_update_mapping"][
            "default"
        ] = default_payment_status_update_mapping()
        # To avoid duplicating the title and help text for each item
        del data["properties"]["payment_status_update_mapping"]["items"]["title"]
        del data["properties"]["payment_status_update_mapping"]["items"]["description"]
        return data


@register(PLUGIN_IDENTIFIER)
class StufZDSPaymentsRegistration(StufZDSRegistration):
    verbose_name = _("StUF-ZDS (payments)")
    configuration_options = ZaakPaymentOptionsSerializer

    def get_extra_payment_variables(
        self, submission: "Submission", options: ZaakOptions
    ):
        key_mapping = {
            mapping["form_variable"]: mapping["stuf_name"]
            for mapping in options["payment_status_update_mapping"]
        }
        return {
            key_mapping[variable.key]: prepare_value(variable.initial_value)
            for variable in get_static_variables(
                submission=submission,
                variables_registry=variables_registry,
            )
            if variable.key
            in [
                "payment_completed",
                "payment_amount",
                "payment_public_order_ids",
                "provider_payment_ids",
            ]
            and variable.key in key_mapping
        }

    def get_extra_data(
        self, submission: Submission, options: ZaakOptions
    ) -> dict[str, Any]:
        """
        Overridden to ensure the extra payment variables are sent as extraElementen
        when creating the Zaak
        """
        data = super().get_extra_data(submission, options)
        payment_extra = self.get_extra_payment_variables(submission, options)
        return {**data, **payment_extra}

    def update_payment_status(self, submission: "Submission", options: ZaakOptions):
        extra_data = self.get_extra_data(submission, options)
        # The extraElement tag of StUF-ZDS expects primitive types
        extra_data = flatten_data(extra_data)

        class LangInjection:
            """Ensures the first extra element is the submission language
            and isn't shadowed by a form field with the same key"""

            def items(self):
                yield ("language_code", submission.language_code)
                yield from extra_data.items()

        with get_client(options) as client:
            client.set_zaak_payment(
                submission.registration_result["zaak"],
                extra=LangInjection(),
            )
