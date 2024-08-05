from decimal import Decimal
from pathlib import Path
from textwrap import dedent

from django.test import TestCase

from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.constants import RegistrationAttribute
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.stuf_zds.models import StufZDSConfig
from stuf.tests.factories import StufServiceFactory

from stuf_zds_payments.client import ZaakOptions
from stuf_zds_payments.plugin import (
    StufZDSPaymentsRegistration,
    default_payment_status_update_mapping,
)

TESTS_DIR = Path(__file__).parent.resolve()


class StufZDSPaymentsRegistrationTestCase(OFVCRMixin, TestCase):
    VCR_TEST_FILES = TESTS_DIR / "data"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.save()

        cls.options = ZaakOptions(
            payment_status_update_mapping=default_payment_status_update_mapping(),
            zds_zaaktype_code="foo",
            zds_zaaktype_omschrijving="bar",
            zds_zaaktype_status_code="baz",
            zds_zaaktype_status_omschrijving="foo",
            zds_documenttype_omschrijving_inzending="foo",
            zds_zaakdoc_vertrouwelijkheid="GEHEIM",
            omschrijving="foo",
            referentienummer="foo",
        )
        cls.plugin = StufZDSPaymentsRegistration("test")

        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
                {
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                {
                    "key": "extra",
                },
                {
                    "key": "language_code",
                },
            ],
            form__name="my-form",
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": [52.36673378967122, 4.893164274470299],
                "extra": "BuzzBazz",
            },
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        # can't pass this as part of `SubmissionFactory.from_components`
        cls.submission.price = Decimal("40.00")
        cls.submission.save()
        SubmissionPaymentFactory.create(
            submission=cls.submission,
            amount=Decimal("25.00"),
            public_order_id="foo",
            status=PaymentStatus.completed,
        )
        SubmissionPaymentFactory.create(
            submission=cls.submission,
            amount=Decimal("15.00"),
            public_order_id="bar",
            status=PaymentStatus.completed,
        )

    def test_set_zaak_payment(self):
        self.plugin.update_payment_status(self.submission, self.options)

        request_body = self.cassette.requests[0].body.decode("utf-8")

        expected = dedent(
            """\
            <StUF:extraElementen>

            <StUF:extraElement naam="language_code">en</StUF:extraElement>

            <StUF:extraElement naam="extra">BuzzBazz</StUF:extraElement>

            <StUF:extraElement naam="payment_completed">true</StUF:extraElement>

            <StUF:extraElement naam="payment_amount">40.0</StUF:extraElement>

            <StUF:extraElement naam="payment_public_order_ids.0">foo</StUF:extraElement>

            <StUF:extraElement naam="payment_public_order_ids.1">bar</StUF:extraElement>

            </StUF:extraElementen>"""
        )

        self.assertIn(expected, request_body)

    def test_set_zaak_payment_incorrect_payment_status_update_mapping(self):
        """
        Non-existent fields in the payment_status_update_mapping should be ignored
        """
        options = ZaakOptions(
            payment_status_update_mapping=[
                {"form_variable": "payment_amount", "stuf_name": "paymentAmount"},
                {"form_variable": "non-existent-field", "stuf_name": "foo"},
            ],
            zds_zaaktype_code="foo",
            zds_zaaktype_omschrijving="bar",
            zds_zaaktype_status_code="baz",
            zds_zaaktype_status_omschrijving="foo",
            zds_documenttype_omschrijving_inzending="foo",
            zds_zaakdoc_vertrouwelijkheid="GEHEIM",
            omschrijving="foo",
            referentienummer="foo",
        )
        self.plugin.update_payment_status(self.submission, options)

        request_body = self.cassette.requests[0].body.decode("utf-8")
        expected = dedent(
            """\
            <StUF:extraElementen>

            <StUF:extraElement naam="language_code">en</StUF:extraElement>

            <StUF:extraElement naam="extra">BuzzBazz</StUF:extraElement>

            <StUF:extraElement naam="paymentAmount">40.0</StUF:extraElement>

            </StUF:extraElementen>"""
        )

        self.assertIn(expected, request_body)

    def test_register_submission_with_payment(self):
        """
        Assert that payment attributes are included when creating the zaak, in case
        the registration is deferred until the payment is received
        """
        self.plugin.register_submission(self.submission, self.options)

        request_body = self.cassette.requests[0].body.decode("utf-8")
        expected = dedent(
            """\
            <StUF:extraElementen>

            <StUF:extraElement naam="language_code">en</StUF:extraElement>

            <StUF:extraElement naam="extra">BuzzBazz</StUF:extraElement>

            <StUF:extraElement naam="payment_completed">true</StUF:extraElement>

            <StUF:extraElement naam="payment_amount">40.0</StUF:extraElement>

            <StUF:extraElement naam="payment_public_order_ids.0">foo</StUF:extraElement>

            <StUF:extraElement naam="payment_public_order_ids.1">bar</StUF:extraElement>

            </StUF:extraElementen>"""
        )

        self.assertIn(expected, request_body)
