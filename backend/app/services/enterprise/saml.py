"""Enterprise SSO/SAML authentication."""

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import defusedxml.ElementTree as DefusedET
import structlog


logger = structlog.get_logger()


@dataclass
class SAMLConfig:
    """SAML configuration for an organization."""

    entity_id: str
    sso_url: str
    slo_url: str | None
    certificate: str
    attribute_mapping: dict[str, str]
    allow_idp_initiated: bool = True


@dataclass
class SAMLAssertion:
    """Parsed SAML assertion."""

    subject_id: str
    email: str
    attributes: dict[str, Any]
    session_index: str | None
    issued_at: datetime
    valid_until: datetime
    issuer: str


class SAMLService:
    """Service for SAML-based SSO authentication."""

    def __init__(self):
        self.sp_entity_id = "https://app.complianceagent.ai/saml/metadata"
        self.acs_url = "https://app.complianceagent.ai/api/v1/auth/saml/acs"
        self.slo_url = "https://app.complianceagent.ai/api/v1/auth/saml/slo"

    def generate_auth_request(
        self,
        config: SAMLConfig,
        relay_state: str | None = None,
    ) -> dict[str, str]:
        """Generate SAML authentication request."""
        request_id = f"_complianceagent_{datetime.now(UTC).timestamp()}"
        issue_instant = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        saml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{config.sso_url}"
    AssertionConsumerServiceURL="{self.acs_url}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy
        Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        AllowCreate="true"/>
</samlp:AuthnRequest>"""

        encoded_request = base64.b64encode(saml_request.encode()).decode()

        return {
            "sso_url": config.sso_url,
            "saml_request": encoded_request,
            "relay_state": relay_state or "",
            "request_id": request_id,
        }

    def parse_response(
        self,
        saml_response: str,
        config: SAMLConfig,
    ) -> SAMLAssertion:
        """Parse and validate SAML response."""
        try:
            decoded = base64.b64decode(saml_response)
            root = DefusedET.fromstring(decoded)
        except Exception as e:
            msg = f"Invalid SAML response: {e}"
            raise ValueError(msg) from e

        ns = {
            "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        }

        status = root.find(".//samlp:StatusCode", ns)
        if status is not None:
            status_value = status.get("Value", "")
            if "Success" not in status_value:
                msg = f"SAML authentication failed: {status_value}"
                raise ValueError(msg)

        assertion = root.find(".//saml:Assertion", ns)
        if assertion is None:
            msg = "No assertion in SAML response"
            raise ValueError(msg)

        subject = assertion.find(".//saml:Subject/saml:NameID", ns)
        subject_id = subject.text if subject is not None else ""

        conditions = assertion.find(".//saml:Conditions", ns)
        not_before = conditions.get("NotBefore") if conditions is not None else None
        not_after = conditions.get("NotOnOrAfter") if conditions is not None else None

        attributes = {}
        attr_statement = assertion.find(".//saml:AttributeStatement", ns)
        if attr_statement is not None:
            for attr in attr_statement.findall("saml:Attribute", ns):
                name = attr.get("Name", "")
                value = attr.find("saml:AttributeValue", ns)
                if value is not None and value.text:
                    mapped_name = config.attribute_mapping.get(name, name)
                    attributes[mapped_name] = value.text

        issuer = assertion.find("saml:Issuer", ns)
        issuer_value = issuer.text if issuer is not None else ""

        if issuer_value != config.entity_id:
            msg = f"Invalid issuer: {issuer_value}"
            raise ValueError(msg)

        issued_at = datetime.now(UTC)
        valid_until = datetime.now(UTC)

        if not_before:
            issued_at = datetime.fromisoformat(not_before)
        if not_after:
            valid_until = datetime.fromisoformat(not_after)

        now = datetime.now(UTC)
        if now < issued_at or now > valid_until:
            msg = "SAML assertion is outside valid time window"
            raise ValueError(msg)

        return SAMLAssertion(
            subject_id=subject_id,
            email=attributes.get("email", subject_id),
            attributes=attributes,
            session_index=None,
            issued_at=issued_at,
            valid_until=valid_until,
            issuer=issuer_value,
        )

    def generate_metadata(self) -> str:
        """Generate SP metadata XML."""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{self.sp_entity_id}">
    <md:SPSSODescriptor
        AuthnRequestsSigned="false"
        WantAssertionsSigned="true"
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{self.acs_url}"
            index="0"
            isDefault="true"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""


saml_service = SAMLService()
