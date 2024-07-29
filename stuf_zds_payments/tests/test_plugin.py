from decimal import Decimal
from pathlib import Path

from django.test import TestCase

from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.stuf_zds.models import StufZDSConfig
from stuf.tests.factories import StufServiceFactory

from stuf_zds_payments.client import ZaakOptions
from stuf_zds_payments.plugin import (
    StufZDSPaymentsRegistration,
    get_payment_status_update_text,
)

TESTS_DIR = Path(__file__).parent.resolve()


class StufFZDSPaymentsRegistrationTestCase(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TESTS_DIR / "data"

    def setUp(self):
        super().setUp()

        self.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = self.zds_service
        config.save()

        self.options = ZaakOptions(
            payment_status_update_xml=get_payment_status_update_text(),
            zds_zaaktype_code="foo",
            zds_zaaktype_omschrijving="bar",
            zds_zaaktype_status_code="baz",
            zds_zaaktype_status_omschrijving="foo",
            zds_documenttype_omschrijving_inzending="foo",
            zds_zaakdoc_vertrouwelijkheid="GEHEIM",
            omschrijving="foo",
            referentienummer="foo",
        )
        self.plugin = StufZDSPaymentsRegistration("test")

    def test_set_zaak_payment(self):
        submission = SubmissionFactory.create(
            public_registration_reference="abc123",
            registration_success=True,
            registration_result={"zaak": "1234"},
            price=Decimal("40.00"),
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("25.00"),
            public_order_id="foo",
            status=PaymentStatus.completed,
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("15.00"),
            public_order_id="bar",
            status=PaymentStatus.completed,
        )

        self.plugin.update_payment_status(submission, self.options)

        request_body = self.cassette.requests[0].body.decode("utf-8")
        expected = """<StUF:extraElementen>
    <StUF:extraElement naam="payment_completed">true</StUF:extraElement>
    <StUF:extraElement naam="payment_amount">40.0</StUF:extraElement>
    <StUF:extraElement naam="payment_public_order_ids">foo bar</StUF:extraElement>
</StUF:extraElementen>"""

        self.assertIn(expected, request_body)
