from functools import partial

from django.utils import timezone

from openforms.logging import logevent
from stuf.constants import EndpointType
from stuf.models import StufService
from stuf.service_client_factory import ServiceClientFactory, get_client_init_kwargs
from stuf.stuf_zds.client import (
    Client as _Client,
    NoServiceConfigured,
    PaymentStatus,
    ZaakOptions,
    fmt_soap_date,
)
from stuf.stuf_zds.models import StufZDSConfig


class ZaakOptions(ZaakOptions):
    payment_status_update_xml: dict


class Client(_Client):
    def set_zaak_payment(
        self,
        zaak_identificatie: str,
        partial: bool = False,
        payment_status_update_xml: str | None = None,
    ) -> dict:
        data = {
            "betalings_indicatie": (
                PaymentStatus.PARTIAL if partial else PaymentStatus.FULL
            ),
            "laatste_betaaldatum": fmt_soap_date(timezone.now()),
            "payment_status_update_xml": payment_status_update_xml,
        }
        return self.partial_update_zaak(zaak_identificatie, data)

    def partial_update_zaak(self, zaak_identificatie: str, zaak_data: dict) -> None:
        context = {
            "zaak_identificatie": zaak_identificatie,
            **zaak_data,
        }

        self.execute_call(
            soap_action="updateZaak_Lk01",
            template="registrations/contrib/stuf_zds_payments/updateZaak.xml",
            context=context,
            endpoint_type=EndpointType.ontvang_asynchroon,
        )


def get_client(options: ZaakOptions):
    config = StufZDSConfig.get_solo()
    if not (service := config.service):
        raise NoServiceConfigured("You must configure a service!")
    return StufZDSClient(service, options)


def StufZDSClient(service: StufService, options: ZaakOptions) -> "Client":
    factory = ServiceClientFactory(service)
    init_kwargs = get_client_init_kwargs(
        service,
        request_log_hook=partial(logevent.stuf_zds_request, service),
    )

    return Client.configure_from(
        factory,
        options=options,
        failure_log_callback=partial(logevent.stuf_zds_failure_response, service),
        success_log_callback=partial(logevent.stuf_zds_success_response, service),
        **init_kwargs,
    )
