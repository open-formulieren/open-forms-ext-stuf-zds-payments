from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StufZdsPaymentsConfig(AppConfig):
    name = "stuf_zds_payments"
    label = "registration_stuf_zds_payments"
    verbose_name = _("StUF-ZDS (extra payments) registration plugin")

    def ready(self):
        from . import plugin  # noqa
