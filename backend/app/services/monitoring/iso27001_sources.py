"""ISO 27001 (Information Security Management System) regulatory source implementations."""

import re
from typing import Any

import structlog
from bs4 import BeautifulSoup

from app.models.regulation import Jurisdiction, RegulatoryFramework, RegulatorySource
from app.services.monitoring.crawler import RegulatoryCrawler


logger = structlog.get_logger()


# ISO 27001 source definitions
ISO27001_SOURCES = [
    {
        "id": "iso27001-iso-store",
        "name": "ISO 27001:2022 Standard",
        "description": "Official ISO/IEC 27001:2022 Information Security Management standard",
        "url": "https://www.iso.org/standard/27001",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.ISO27001,
        "parser_type": "html",
        "type": "official",
        "parser_config": {},
    },
    {
        "id": "iso27001-iso-guidance",
        "name": "ISO 27002:2022 Code of Practice",
        "description": "ISO/IEC 27002:2022 Information security controls guidance",
        "url": "https://www.iso.org/standard/75652.html",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.ISO27001,
        "parser_type": "html",
        "type": "guidance",
        "parser_config": {},
    },
    {
        "id": "iso27001-enisa",
        "name": "ENISA ISO 27001 Resources",
        "description": "European Union Agency for Cybersecurity ISO 27001 implementation resources",
        "url": "https://www.enisa.europa.eu/topics/standards",
        "jurisdiction": Jurisdiction.EU,
        "framework": RegulatoryFramework.ISO27001,
        "parser_type": "html",
        "type": "guidance",
        "parser_config": {},
    },
    {
        "id": "iso27001-nist-mapping",
        "name": "NIST to ISO 27001 Mapping",
        "description": "NIST Cybersecurity Framework to ISO 27001 mapping",
        "url": "https://www.nist.gov/cyberframework",
        "jurisdiction": Jurisdiction.GLOBAL,
        "framework": RegulatoryFramework.ISO27001,
        "parser_type": "html",
        "type": "supplemental",
        "parser_config": {},
    },
]


# ISO 27001:2022 Control Categories (Annex A)
ISO27001_CONTROL_CATEGORIES = {
    "organizational": {
        "code": "A.5",
        "name": "Organizational Controls",
        "description": "Controls related to organizational aspects of information security",
        "control_count": 37,
    },
    "people": {
        "code": "A.6",
        "name": "People Controls",
        "description": "Controls related to people/human resources security",
        "control_count": 8,
    },
    "physical": {
        "code": "A.7",
        "name": "Physical Controls",
        "description": "Controls related to physical security",
        "control_count": 14,
    },
    "technological": {
        "code": "A.8",
        "name": "Technological Controls",
        "description": "Controls related to technology and technical security",
        "control_count": 34,
    },
}


# ISO 27001:2022 Requirements (Clauses 4-10) and Annex A Controls
ISO27001_REQUIREMENTS = [
    # Clause 4 - Context of the organization
    {
        "id": "ISO27001-4.1",
        "clause": "4",
        "name": "Understanding the organization and its context",
        "description": "Determine external and internal issues relevant to the ISMS purpose and strategic direction",
        "applies_to": ["mandatory"],
        "category": "context",
    },
    {
        "id": "ISO27001-4.2",
        "clause": "4",
        "name": "Understanding needs and expectations of interested parties",
        "description": "Determine interested parties relevant to ISMS and their requirements",
        "applies_to": ["mandatory"],
        "category": "context",
    },
    {
        "id": "ISO27001-4.3",
        "clause": "4",
        "name": "Determining the scope of the ISMS",
        "description": "Define boundaries and applicability of the ISMS",
        "applies_to": ["mandatory"],
        "category": "context",
    },
    {
        "id": "ISO27001-4.4",
        "clause": "4",
        "name": "Information security management system",
        "description": "Establish, implement, maintain, and continually improve an ISMS",
        "applies_to": ["mandatory"],
        "category": "context",
    },
    # Clause 5 - Leadership
    {
        "id": "ISO27001-5.1",
        "clause": "5",
        "name": "Leadership and commitment",
        "description": "Top management shall demonstrate leadership and commitment to the ISMS",
        "applies_to": ["mandatory"],
        "category": "leadership",
    },
    {
        "id": "ISO27001-5.2",
        "clause": "5",
        "name": "Policy",
        "description": "Establish an information security policy appropriate to the organization",
        "applies_to": ["mandatory"],
        "category": "leadership",
    },
    {
        "id": "ISO27001-5.3",
        "clause": "5",
        "name": "Organizational roles, responsibilities and authorities",
        "description": "Assign and communicate responsibilities and authorities for ISMS roles",
        "applies_to": ["mandatory"],
        "category": "leadership",
    },
    # Clause 6 - Planning
    {
        "id": "ISO27001-6.1.1",
        "clause": "6",
        "name": "Actions to address risks and opportunities",
        "description": "Plan actions to address risks and opportunities to the ISMS",
        "applies_to": ["mandatory"],
        "category": "planning",
    },
    {
        "id": "ISO27001-6.1.2",
        "clause": "6",
        "name": "Information security risk assessment",
        "description": "Define and apply an information security risk assessment process",
        "applies_to": ["mandatory"],
        "category": "planning",
    },
    {
        "id": "ISO27001-6.1.3",
        "clause": "6",
        "name": "Information security risk treatment",
        "description": "Define and apply an information security risk treatment process",
        "applies_to": ["mandatory"],
        "category": "planning",
    },
    {
        "id": "ISO27001-6.2",
        "clause": "6",
        "name": "Information security objectives and planning",
        "description": "Establish information security objectives at relevant functions and levels",
        "applies_to": ["mandatory"],
        "category": "planning",
    },
    {
        "id": "ISO27001-6.3",
        "clause": "6",
        "name": "Planning of changes",
        "description": "Plan changes to the ISMS in a controlled manner",
        "applies_to": ["mandatory"],
        "category": "planning",
    },
    # Clause 7 - Support
    {
        "id": "ISO27001-7.1",
        "clause": "7",
        "name": "Resources",
        "description": "Determine and provide resources needed for ISMS",
        "applies_to": ["mandatory"],
        "category": "support",
    },
    {
        "id": "ISO27001-7.2",
        "clause": "7",
        "name": "Competence",
        "description": "Determine competence needed for persons affecting ISMS performance",
        "applies_to": ["mandatory"],
        "category": "support",
    },
    {
        "id": "ISO27001-7.3",
        "clause": "7",
        "name": "Awareness",
        "description": "Ensure persons are aware of the information security policy and their contribution",
        "applies_to": ["mandatory"],
        "category": "support",
    },
    {
        "id": "ISO27001-7.4",
        "clause": "7",
        "name": "Communication",
        "description": "Determine internal and external communications relevant to the ISMS",
        "applies_to": ["mandatory"],
        "category": "support",
    },
    {
        "id": "ISO27001-7.5",
        "clause": "7",
        "name": "Documented information",
        "description": "Include documented information required by the standard and determined by the organization",
        "applies_to": ["mandatory"],
        "category": "support",
    },
    # Clause 8 - Operation
    {
        "id": "ISO27001-8.1",
        "clause": "8",
        "name": "Operational planning and control",
        "description": "Plan, implement, and control processes needed to meet requirements",
        "applies_to": ["mandatory"],
        "category": "operation",
    },
    {
        "id": "ISO27001-8.2",
        "clause": "8",
        "name": "Information security risk assessment",
        "description": "Perform information security risk assessments at planned intervals",
        "applies_to": ["mandatory"],
        "category": "operation",
    },
    {
        "id": "ISO27001-8.3",
        "clause": "8",
        "name": "Information security risk treatment",
        "description": "Implement the information security risk treatment plan",
        "applies_to": ["mandatory"],
        "category": "operation",
    },
    # Clause 9 - Performance evaluation
    {
        "id": "ISO27001-9.1",
        "clause": "9",
        "name": "Monitoring, measurement, analysis and evaluation",
        "description": "Evaluate ISMS performance and effectiveness",
        "applies_to": ["mandatory"],
        "category": "performance",
    },
    {
        "id": "ISO27001-9.2",
        "clause": "9",
        "name": "Internal audit",
        "description": "Conduct internal audits at planned intervals",
        "applies_to": ["mandatory"],
        "category": "performance",
    },
    {
        "id": "ISO27001-9.3",
        "clause": "9",
        "name": "Management review",
        "description": "Review ISMS at planned intervals to ensure continuing suitability",
        "applies_to": ["mandatory"],
        "category": "performance",
    },
    # Clause 10 - Improvement
    {
        "id": "ISO27001-10.1",
        "clause": "10",
        "name": "Continual improvement",
        "description": "Continually improve the suitability, adequacy and effectiveness of the ISMS",
        "applies_to": ["mandatory"],
        "category": "improvement",
    },
    {
        "id": "ISO27001-10.2",
        "clause": "10",
        "name": "Nonconformity and corrective action",
        "description": "React to nonconformities and take corrective action",
        "applies_to": ["mandatory"],
        "category": "improvement",
    },
    # Annex A - Organizational Controls (A.5)
    {
        "id": "ISO27001-A.5.1",
        "clause": "A.5",
        "name": "Policies for information security",
        "description": "Information security policy and topic-specific policies shall be defined and approved",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.2",
        "clause": "A.5",
        "name": "Information security roles and responsibilities",
        "description": "Information security roles and responsibilities shall be defined and allocated",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.3",
        "clause": "A.5",
        "name": "Segregation of duties",
        "description": "Conflicting duties and areas of responsibility shall be segregated",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.4",
        "clause": "A.5",
        "name": "Management responsibilities",
        "description": "Management shall require personnel to apply information security in accordance with policies",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.5",
        "clause": "A.5",
        "name": "Contact with authorities",
        "description": "Appropriate contacts with relevant authorities shall be maintained",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.6",
        "clause": "A.5",
        "name": "Contact with special interest groups",
        "description": "Appropriate contacts with special interest groups shall be maintained",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.7",
        "clause": "A.5",
        "name": "Threat intelligence",
        "description": "Information relating to information security threats shall be collected and analysed",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.8",
        "clause": "A.5",
        "name": "Information security in project management",
        "description": "Information security shall be integrated into project management",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.9",
        "clause": "A.5",
        "name": "Inventory of information and other associated assets",
        "description": "An inventory of information and other associated assets shall be developed and maintained",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.10",
        "clause": "A.5",
        "name": "Acceptable use of information and other associated assets",
        "description": "Rules for acceptable use shall be identified, documented and implemented",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.11",
        "clause": "A.5",
        "name": "Return of assets",
        "description": "Personnel shall return all organizational assets upon termination",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.12",
        "clause": "A.5",
        "name": "Classification of information",
        "description": "Information shall be classified according to organizational information security needs",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.13",
        "clause": "A.5",
        "name": "Labelling of information",
        "description": "An appropriate set of procedures for information labelling shall be implemented",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.14",
        "clause": "A.5",
        "name": "Information transfer",
        "description": "Information transfer rules shall be in place for all types of transfer facilities",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.15",
        "clause": "A.5",
        "name": "Access control",
        "description": "Rules to control physical and logical access shall be established and implemented",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.16",
        "clause": "A.5",
        "name": "Identity management",
        "description": "The full lifecycle of identities shall be managed",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.17",
        "clause": "A.5",
        "name": "Authentication information",
        "description": "Allocation and management of authentication information shall be controlled",
        "applies_to": ["control"],
        "category": "organizational",
    },
    {
        "id": "ISO27001-A.5.18",
        "clause": "A.5",
        "name": "Access rights",
        "description": "Access rights shall be provisioned, reviewed, modified and removed in accordance with policies",
        "applies_to": ["control"],
        "category": "organizational",
    },
    # Annex A - People Controls (A.6)
    {
        "id": "ISO27001-A.6.1",
        "clause": "A.6",
        "name": "Screening",
        "description": "Background verification checks shall be carried out on candidates for employment",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.2",
        "clause": "A.6",
        "name": "Terms and conditions of employment",
        "description": "Contractual agreements shall state responsibilities for information security",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.3",
        "clause": "A.6",
        "name": "Information security awareness, education and training",
        "description": "Personnel shall receive appropriate awareness and training updates",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.4",
        "clause": "A.6",
        "name": "Disciplinary process",
        "description": "A disciplinary process shall be implemented for personnel who commit information security breaches",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.5",
        "clause": "A.6",
        "name": "Responsibilities after termination or change of employment",
        "description": "Information security responsibilities that remain valid after termination shall be communicated",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.6",
        "clause": "A.6",
        "name": "Confidentiality or non-disclosure agreements",
        "description": "Confidentiality agreements shall reflect the organization's needs for protecting information",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.7",
        "clause": "A.6",
        "name": "Remote working",
        "description": "Security measures shall be implemented when personnel are working remotely",
        "applies_to": ["control"],
        "category": "people",
    },
    {
        "id": "ISO27001-A.6.8",
        "clause": "A.6",
        "name": "Information security event reporting",
        "description": "Personnel shall report observed or suspected information security events",
        "applies_to": ["control"],
        "category": "people",
    },
    # Annex A - Physical Controls (A.7)
    {
        "id": "ISO27001-A.7.1",
        "clause": "A.7",
        "name": "Physical security perimeters",
        "description": "Security perimeters shall be defined and used to protect areas containing information",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.2",
        "clause": "A.7",
        "name": "Physical entry",
        "description": "Secure areas shall be protected by appropriate entry controls",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.3",
        "clause": "A.7",
        "name": "Securing offices, rooms and facilities",
        "description": "Physical security for offices, rooms and facilities shall be designed and implemented",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.4",
        "clause": "A.7",
        "name": "Physical security monitoring",
        "description": "Premises shall be continuously monitored for unauthorized physical access",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.5",
        "clause": "A.7",
        "name": "Protecting against physical and environmental threats",
        "description": "Protection against physical and environmental threats shall be implemented",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.6",
        "clause": "A.7",
        "name": "Working in secure areas",
        "description": "Security measures for working in secure areas shall be implemented",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.7",
        "clause": "A.7",
        "name": "Clear desk and clear screen",
        "description": "Clear desk rules and clear screen rules shall be defined and enforced",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.8",
        "clause": "A.7",
        "name": "Equipment siting and protection",
        "description": "Equipment shall be sited securely and protected",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.9",
        "clause": "A.7",
        "name": "Security of assets off-premises",
        "description": "Off-site assets shall be protected",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.10",
        "clause": "A.7",
        "name": "Storage media",
        "description": "Storage media shall be managed through their lifecycle of acquisition, use, transport and disposal",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.11",
        "clause": "A.7",
        "name": "Supporting utilities",
        "description": "Equipment shall be protected from power failures and other disruptions",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.12",
        "clause": "A.7",
        "name": "Cabling security",
        "description": "Cables carrying power or data shall be protected from interception or damage",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.13",
        "clause": "A.7",
        "name": "Equipment maintenance",
        "description": "Equipment shall be maintained correctly to ensure availability and integrity",
        "applies_to": ["control"],
        "category": "physical",
    },
    {
        "id": "ISO27001-A.7.14",
        "clause": "A.7",
        "name": "Secure disposal or re-use of equipment",
        "description": "Items of equipment containing storage media shall be verified prior to disposal",
        "applies_to": ["control"],
        "category": "physical",
    },
    # Annex A - Technological Controls (A.8)
    {
        "id": "ISO27001-A.8.1",
        "clause": "A.8",
        "name": "User endpoint devices",
        "description": "Information stored on, processed by or accessible via user endpoint devices shall be protected",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.2",
        "clause": "A.8",
        "name": "Privileged access rights",
        "description": "The allocation and use of privileged access rights shall be restricted and managed",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.3",
        "clause": "A.8",
        "name": "Information access restriction",
        "description": "Access to information and application system functions shall be restricted in accordance with policy",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.4",
        "clause": "A.8",
        "name": "Access to source code",
        "description": "Read and write access to source code and development tools shall be appropriately managed",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.5",
        "clause": "A.8",
        "name": "Secure authentication",
        "description": "Secure authentication technologies and procedures shall be implemented",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.6",
        "clause": "A.8",
        "name": "Capacity management",
        "description": "The use of resources shall be monitored and adjusted in line with requirements",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.7",
        "clause": "A.8",
        "name": "Protection against malware",
        "description": "Protection against malware shall be implemented and supported by appropriate user awareness",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.8",
        "clause": "A.8",
        "name": "Management of technical vulnerabilities",
        "description": "Information about technical vulnerabilities shall be obtained and appropriate measures taken",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.9",
        "clause": "A.8",
        "name": "Configuration management",
        "description": "Configurations shall be established, documented, implemented, monitored and reviewed",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.10",
        "clause": "A.8",
        "name": "Information deletion",
        "description": "Information stored in systems and devices shall be deleted when no longer required",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.11",
        "clause": "A.8",
        "name": "Data masking",
        "description": "Data masking shall be used in accordance with the organization's policies",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.12",
        "clause": "A.8",
        "name": "Data leakage prevention",
        "description": "Data leakage prevention measures shall be applied to systems and networks",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.13",
        "clause": "A.8",
        "name": "Information backup",
        "description": "Backup copies of information shall be maintained and regularly tested",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.14",
        "clause": "A.8",
        "name": "Redundancy of information processing facilities",
        "description": "Information processing facilities shall be implemented with redundancy",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.15",
        "clause": "A.8",
        "name": "Logging",
        "description": "Logs that record activities and security events shall be produced and retained",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.16",
        "clause": "A.8",
        "name": "Monitoring activities",
        "description": "Networks, systems and applications shall be monitored for anomalous behaviour",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.17",
        "clause": "A.8",
        "name": "Clock synchronization",
        "description": "The clocks of information processing systems shall be synchronized to approved time sources",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.18",
        "clause": "A.8",
        "name": "Use of privileged utility programs",
        "description": "The use of utility programs that can override system and application controls shall be restricted",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.19",
        "clause": "A.8",
        "name": "Installation of software on operational systems",
        "description": "Procedures shall be implemented to securely manage software installation",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.20",
        "clause": "A.8",
        "name": "Networks security",
        "description": "Networks and network devices shall be secured, managed and controlled",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.21",
        "clause": "A.8",
        "name": "Security of network services",
        "description": "Security mechanisms and service levels shall be identified and incorporated in agreements",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.22",
        "clause": "A.8",
        "name": "Segregation of networks",
        "description": "Groups of information services, users and information systems shall be segregated",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.23",
        "clause": "A.8",
        "name": "Web filtering",
        "description": "Access to external websites shall be managed to reduce exposure to malicious content",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.24",
        "clause": "A.8",
        "name": "Use of cryptography",
        "description": "Rules for the effective use of cryptography shall be defined and implemented",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.25",
        "clause": "A.8",
        "name": "Secure development life cycle",
        "description": "Rules for secure development shall be established and applied",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.26",
        "clause": "A.8",
        "name": "Application security requirements",
        "description": "Information security requirements shall be identified and specified when developing applications",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.27",
        "clause": "A.8",
        "name": "Secure system architecture and engineering principles",
        "description": "Principles for engineering secure systems shall be established and applied",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.28",
        "clause": "A.8",
        "name": "Secure coding",
        "description": "Secure coding principles shall be applied to software development",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.29",
        "clause": "A.8",
        "name": "Security testing in development and acceptance",
        "description": "Security testing processes shall be defined and implemented in the development lifecycle",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.30",
        "clause": "A.8",
        "name": "Outsourced development",
        "description": "The organization shall direct, monitor and review outsourced system development activities",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.31",
        "clause": "A.8",
        "name": "Separation of development, test and production environments",
        "description": "Development, testing and production environments shall be separated and secured",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.32",
        "clause": "A.8",
        "name": "Change management",
        "description": "Changes to information processing facilities and systems shall follow change management procedures",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.33",
        "clause": "A.8",
        "name": "Test information",
        "description": "Test information shall be appropriately selected, protected and managed",
        "applies_to": ["control"],
        "category": "technological",
    },
    {
        "id": "ISO27001-A.8.34",
        "clause": "A.8",
        "name": "Protection of information systems during audit testing",
        "description": "Audit tests shall be planned to minimize impact on operational systems",
        "applies_to": ["control"],
        "category": "technological",
    },
]


class ISO27001Parser:
    """Parser for ISO 27001-related documents."""

    def __init__(self):
        self.clause_pattern = re.compile(r"Clause\s+(\d+(?:\.\d+)?)", re.IGNORECASE)
        self.control_pattern = re.compile(r"A\.(\d+\.\d+)", re.IGNORECASE)

    def parse_iso_page(self, content: str) -> dict[str, Any]:
        """Parse ISO 27001 guidance page."""
        soup = BeautifulSoup(content, "lxml")

        result = {
            "title": "",
            "standards": [],
            "updates": [],
        }

        main_content = soup.find("main") or soup.find("div", class_="content")
        if main_content:
            title = main_content.find("h1")
            if title:
                result["title"] = title.get_text(strip=True)

            for link in main_content.select("a[href*='iso.org/standard']"):
                text = link.get_text(strip=True)
                href = link.get("href", "")
                if text:
                    result["standards"].append({
                        "title": text,
                        "url": href,
                    })

        return result

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all ISO 27001 requirements for database initialization."""
        return ISO27001_REQUIREMENTS

    def get_requirements_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get ISO 27001 requirements filtered by category."""
        return [
            req for req in ISO27001_REQUIREMENTS
            if req["category"] == category
        ]


class ISO27001SourceMonitor:
    """Monitors ISO 27001 regulatory sources."""

    def __init__(self):
        self.crawler = RegulatoryCrawler()
        self.parser = ISO27001Parser()
        self.framework = "iso27001"
        self.sources = ISO27001_SOURCES

    async def check_iso_updates(self, source: RegulatorySource) -> dict[str, Any]:
        """Check ISO for 27001 updates."""
        async with self.crawler:
            result = await self.crawler.crawl(source)

            if result.has_changed:
                parsed = self.parser.parse_iso_page(result.content)
                return {
                    "changed": True,
                    "source": source.name,
                    "parsed": parsed,
                    "standards_count": len(parsed.get("standards", [])),
                }

            return {"changed": False, "source": source.name}

    def get_all_requirements(self) -> list[dict[str, Any]]:
        """Get all ISO 27001 requirements for database initialization."""
        return self.parser.get_all_requirements()

    def get_control_categories(self) -> dict[str, Any]:
        """Get ISO 27001 control categories."""
        return ISO27001_CONTROL_CATEGORIES


def get_iso27001_source_definitions() -> list[dict[str, Any]]:
    """Get predefined ISO 27001 source definitions."""
    return ISO27001_SOURCES


async def initialize_iso27001_sources(db) -> list[RegulatorySource]:
    """Initialize ISO 27001 sources in the database."""
    sources = []

    for source_def in ISO27001_SOURCES:
        source = RegulatorySource(
            name=source_def["name"],
            description=source_def["description"],
            url=source_def["url"],
            jurisdiction=source_def["jurisdiction"],
            framework=source_def["framework"],
            parser_type=source_def["parser_type"],
            parser_config=source_def["parser_config"],
            is_active=True,
            check_interval_hours=168,  # Weekly
        )
        db.add(source)
        sources.append(source)

    await db.flush()
    return sources
