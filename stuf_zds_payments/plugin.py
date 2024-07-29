import logging
from typing import Any

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from openforms.registrations.contrib.stuf_zds.plugin import (
    StufZDSRegistration,
    ZaakOptionsSerializer,
)
from openforms.registrations.registry import register
from openforms.submissions.models import Submission
from openforms.template import render_from_string
from openforms.template.validators import DjangoTemplateValidator
from openforms.variables.service import get_static_variables
from rest_framework import serializers
from stuf.stuf_zds.client import ZaakOptions

from .client import get_client
from .registration_variables import register as variables_registry

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "stuf-zds-create-zaak:ext-utrecht"


def get_payment_status_update_text() -> str:
    return render_to_string(
        "registrations/contrib/stuf_zds_payments/payment_status_update_xml.txt"
    ).strip()


def prepare_value(value: Any):
    match value:
        case bool():
            return "true" if value else "false"
        case list():
            return " ".join(value)
        case float():
            return str(value)
        case _:
            return value


class ZaakPaymentOptionsSerializer(ZaakOptionsSerializer):
    payment_status_update_xml = serializers.CharField(
        label=_("payment status update XML template"),
        help_text=_(
            "This template is evaluated with the submission data and the resulting XML "
            "is sent to the StUF-ZDS with a PATCH to update the payment field."
        ),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        required=False,
    )

    @classmethod
    def display_as_jsonschema(cls):
        data = super().display_as_jsonschema()
        # Workaround because drf_jsonschema_serializer does not pick up defaults
        data["properties"]["payment_status_update_xml"][
            "default"
        ] = get_payment_status_update_text()
        return data


@register(PLUGIN_IDENTIFIER)
class StufZDSPaymentsRegistration(StufZDSRegistration):
    verbose_name = _("StUF-ZDS (payments)")
    configuration_options = ZaakPaymentOptionsSerializer

    def update_payment_status(self, submission: "Submission", options: ZaakOptions):
        values = {
            variable.key: prepare_value(variable.initial_value)
            for variable in get_static_variables(
                submission=submission,
                variables_registry=variables_registry,
            )
            if variable.key
            in ["payment_completed", "payment_amount", "payment_public_order_ids"]
        }

        payment_status_update_xml = render_from_string(
            options["payment_status_update_xml"], values
        )

        with get_client(options) as client:
            client.set_zaak_payment(
                submission.registration_result["zaak"],
                payment_status_update_xml=payment_status_update_xml,
            )
