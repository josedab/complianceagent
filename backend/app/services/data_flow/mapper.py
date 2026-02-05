"""Data Flow Mapper for discovering and mapping cross-border data flows."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.data_flow.models import (
    DataClassification,
    JurisdictionType,
    TransferMechanism,
    ComplianceStatus,
    RiskLevel,
    DataLocation,
    DataFlow,
    DataFlowMap,
    EEA_COUNTRIES,
    EU_ADEQUATE_COUNTRIES,
    DATA_LOCALIZATION_COUNTRIES,
    JURISDICTION_REGULATIONS,
)

logger = structlog.get_logger()


# Cloud provider region mappings
CLOUD_REGION_COUNTRIES: dict[str, str] = {
    # AWS regions
    "us-east-1": "US", "us-east-2": "US", "us-west-1": "US", "us-west-2": "US",
    "eu-west-1": "IE", "eu-west-2": "GB", "eu-west-3": "FR", "eu-central-1": "DE",
    "eu-north-1": "SE", "eu-south-1": "IT",
    "ap-northeast-1": "JP", "ap-northeast-2": "KR", "ap-northeast-3": "JP",
    "ap-southeast-1": "SG", "ap-southeast-2": "AU", "ap-south-1": "IN",
    "sa-east-1": "BR", "ca-central-1": "CA", "me-south-1": "BH",
    "af-south-1": "ZA", "cn-north-1": "CN", "cn-northwest-1": "CN",
    # Azure regions
    "eastus": "US", "eastus2": "US", "westus": "US", "westus2": "US", "centralus": "US",
    "northeurope": "IE", "westeurope": "NL", "uksouth": "GB", "ukwest": "GB",
    "francecentral": "FR", "germanywestcentral": "DE", "swedencentral": "SE",
    "japaneast": "JP", "japanwest": "JP", "koreacentral": "KR",
    "southeastasia": "SG", "australiaeast": "AU", "australiasoutheast": "AU",
    "centralindia": "IN", "brazilsouth": "BR", "canadacentral": "CA",
    "chinaeast": "CN", "chinanorth": "CN",
    # GCP regions
    "us-central1": "US", "us-east1": "US", "us-east4": "US", "us-west1": "US",
    "europe-west1": "BE", "europe-west2": "GB", "europe-west3": "DE",
    "europe-west4": "NL", "europe-west6": "CH", "europe-north1": "FI",
    "asia-east1": "TW", "asia-east2": "HK", "asia-northeast1": "JP",
    "asia-northeast2": "JP", "asia-northeast3": "KR", "asia-south1": "IN",
    "asia-southeast1": "SG", "asia-southeast2": "ID",
    "australia-southeast1": "AU", "southamerica-east1": "BR",
}

# Patterns to detect data types in code
DATA_TYPE_PATTERNS: dict[DataClassification, list[str]] = {
    DataClassification.PII: [
        r"email", r"phone", r"address", r"ssn", r"social.?security",
        r"name", r"birth.?date", r"dob", r"passport", r"driver.?license",
        r"national.?id", r"ip.?address", r"location", r"gps",
    ],
    DataClassification.PHI: [
        r"medical", r"health", r"diagnosis", r"treatment", r"prescription",
        r"patient", r"clinical", r"hipaa", r"phi", r"protected.?health",
    ],
    DataClassification.PCI: [
        r"card.?number", r"credit.?card", r"cvv", r"cvc", r"expir",
        r"cardholder", r"pan", r"payment", r"stripe", r"braintree",
    ],
    DataClassification.SENSITIVE: [
        r"password", r"secret", r"token", r"api.?key", r"credential",
        r"private.?key", r"encryption.?key", r"auth",
    ],
}

# Infrastructure patterns in code
INFRASTRUCTURE_PATTERNS: dict[str, dict[str, Any]] = {
    "aws_s3": {
        "patterns": [r"s3://", r"\.s3\.", r"aws_s3", r"S3Client", r"s3_bucket"],
        "service": "S3",
        "provider": "AWS",
    },
    "aws_rds": {
        "patterns": [r"rds\.", r"aws_rds", r"\.rds\.amazonaws"],
        "service": "RDS",
        "provider": "AWS",
    },
    "aws_dynamodb": {
        "patterns": [r"dynamodb", r"DynamoDB"],
        "service": "DynamoDB",
        "provider": "AWS",
    },
    "azure_blob": {
        "patterns": [r"blob\.core\.windows", r"azure.?storage", r"BlobService"],
        "service": "Blob Storage",
        "provider": "Azure",
    },
    "azure_sql": {
        "patterns": [r"\.database\.windows\.net", r"azure.?sql"],
        "service": "SQL Database",
        "provider": "Azure",
    },
    "gcp_storage": {
        "patterns": [r"storage\.googleapis", r"gcs://", r"google.?cloud.?storage"],
        "service": "Cloud Storage",
        "provider": "GCP",
    },
    "gcp_bigquery": {
        "patterns": [r"bigquery", r"BigQuery"],
        "service": "BigQuery",
        "provider": "GCP",
    },
    "mongodb": {
        "patterns": [r"mongodb://", r"mongodb\+srv://", r"MongoClient"],
        "service": "MongoDB",
        "provider": "MongoDB Atlas",
    },
    "postgresql": {
        "patterns": [r"postgresql://", r"postgres://", r"psycopg"],
        "service": "PostgreSQL",
        "provider": "Self-hosted/Cloud",
    },
    "redis": {
        "patterns": [r"redis://", r"rediss://", r"Redis"],
        "service": "Redis",
        "provider": "Self-hosted/Cloud",
    },
}


class DataFlowMapper:
    """Maps data flows across infrastructure and jurisdictions."""
    
    def __init__(self) -> None:
        self._flow_maps: dict[UUID, DataFlowMap] = {}
        self._locations: dict[UUID, DataLocation] = {}
        self._flows: dict[UUID, DataFlow] = {}
    
    async def discover_data_flows(
        self,
        organization_id: UUID,
        code_files: dict[str, str] | None = None,
        infrastructure_config: dict[str, Any] | None = None,
        manual_locations: list[dict[str, Any]] | None = None,
    ) -> DataFlowMap:
        """Discover data flows from code, infrastructure config, and manual entries."""
        flow_map = DataFlowMap(
            organization_id=organization_id,
        )
        
        # Discover from code analysis
        if code_files:
            locations, flows = await self._analyze_code(code_files)
            flow_map.locations.extend(locations)
            flow_map.flows.extend(flows)
        
        # Discover from infrastructure config
        if infrastructure_config:
            locations, flows = await self._analyze_infrastructure(infrastructure_config)
            flow_map.locations.extend(locations)
            flow_map.flows.extend(flows)
        
        # Add manual locations
        if manual_locations:
            for loc_data in manual_locations:
                location = DataLocation(
                    name=loc_data["name"],
                    description=loc_data.get("description"),
                    country=loc_data["country"],
                    country_code=loc_data["country_code"],
                    region=self._get_region(loc_data["country_code"]),
                    provider=loc_data.get("provider"),
                    service=loc_data.get("service"),
                    data_types=[DataClassification(dt) for dt in loc_data.get("data_types", [])],
                )
                flow_map.locations.append(location)
                self._locations[location.id] = location
        
        # Analyze and enrich flows
        await self._enrich_flows(flow_map)
        
        # Calculate statistics
        self._calculate_statistics(flow_map)
        
        self._flow_maps[flow_map.id] = flow_map
        return flow_map
    
    async def _analyze_code(
        self,
        code_files: dict[str, str],
    ) -> tuple[list[DataLocation], list[DataFlow]]:
        """Analyze code files to discover data locations and flows."""
        locations = []
        flows = []
        discovered_endpoints: dict[str, DataLocation] = {}
        
        for filepath, content in code_files.items():
            # Detect infrastructure endpoints
            for infra_type, config in INFRASTRUCTURE_PATTERNS.items():
                for pattern in config["patterns"]:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Try to extract region
                        region = self._extract_region(content, infra_type)
                        country = CLOUD_REGION_COUNTRIES.get(region, "US")  # Default to US
                        
                        location_key = f"{infra_type}_{region or 'default'}"
                        if location_key not in discovered_endpoints:
                            location = DataLocation(
                                name=f"{config['provider']} {config['service']}",
                                description=f"Discovered from {filepath}",
                                country=self._get_country_name(country),
                                country_code=country,
                                region=self._get_region(country),
                                provider=config["provider"],
                                service=config["service"],
                                data_types=self._detect_data_types(content),
                            )
                            discovered_endpoints[location_key] = location
                            locations.append(location)
                            self._locations[location.id] = location
        
        # Detect data flows between endpoints
        if len(locations) > 1:
            for i, src in enumerate(locations):
                for dest in locations[i+1:]:
                    if src.country_code != dest.country_code:
                        flow = DataFlow(
                            name=f"{src.name} → {dest.name}",
                            source_id=src.id,
                            source_name=src.name,
                            source_country=src.country_code,
                            destination_id=dest.id,
                            destination_name=dest.name,
                            destination_country=dest.country_code,
                            data_types=list(set(src.data_types) & set(dest.data_types)) or src.data_types,
                            detected_from="code_analysis",
                        )
                        flows.append(flow)
                        self._flows[flow.id] = flow
        
        return locations, flows
    
    async def _analyze_infrastructure(
        self,
        config: dict[str, Any],
    ) -> tuple[list[DataLocation], list[DataFlow]]:
        """Analyze infrastructure configuration."""
        locations = []
        flows = []
        
        # Handle Terraform-style config
        if "resource" in config:
            for resource_type, resources in config["resource"].items():
                for name, resource_config in resources.items():
                    location = self._create_location_from_terraform(
                        resource_type, name, resource_config
                    )
                    if location:
                        locations.append(location)
                        self._locations[location.id] = location
        
        # Handle Kubernetes-style config
        if "kind" in config and config.get("kind") in ["Deployment", "StatefulSet", "Service"]:
            location = self._create_location_from_k8s(config)
            if location:
                locations.append(location)
                self._locations[location.id] = location
        
        return locations, flows
    
    def _create_location_from_terraform(
        self,
        resource_type: str,
        name: str,
        config: dict[str, Any],
    ) -> DataLocation | None:
        """Create a data location from Terraform resource."""
        region = config.get("region", config.get("location", ""))
        country = CLOUD_REGION_COUNTRIES.get(region, "US")
        
        provider_map = {
            "aws_": "AWS",
            "azurerm_": "Azure",
            "google_": "GCP",
        }
        
        provider = None
        for prefix, prov in provider_map.items():
            if resource_type.startswith(prefix):
                provider = prov
                break
        
        if not provider:
            return None
        
        return DataLocation(
            name=name,
            description=f"Terraform resource: {resource_type}",
            country=self._get_country_name(country),
            country_code=country,
            region=self._get_region(country),
            provider=provider,
            service=resource_type.split("_")[1] if "_" in resource_type else resource_type,
        )
    
    def _create_location_from_k8s(self, config: dict[str, Any]) -> DataLocation | None:
        """Create a data location from Kubernetes config."""
        metadata = config.get("metadata", {})
        name = metadata.get("name", "Unknown")
        
        # Try to determine region from labels or annotations
        labels = metadata.get("labels", {})
        region = labels.get("topology.kubernetes.io/region", "")
        country = CLOUD_REGION_COUNTRIES.get(region, "US")
        
        return DataLocation(
            name=name,
            description=f"Kubernetes {config.get('kind')}",
            country=self._get_country_name(country),
            country_code=country,
            region=self._get_region(country),
            provider="Kubernetes",
            service=config.get("kind"),
        )
    
    def _extract_region(self, content: str, infra_type: str) -> str | None:
        """Extract cloud region from code content."""
        # AWS region patterns
        aws_region = re.search(r'["\']?(us|eu|ap|sa|ca|me|af|cn)-[a-z]+-\d["\']?', content)
        if aws_region:
            return aws_region.group().strip("'\"")
        
        # Azure region patterns
        azure_region = re.search(r'["\']?(east|west|central|north|south)[a-z]*["\']?', content, re.IGNORECASE)
        if azure_region:
            return azure_region.group().strip("'\"").lower()
        
        # GCP region patterns
        gcp_region = re.search(r'["\']?(us|europe|asia|australia|southamerica)-[a-z]+\d["\']?', content)
        if gcp_region:
            return gcp_region.group().strip("'\"")
        
        return None
    
    def _detect_data_types(self, content: str) -> list[DataClassification]:
        """Detect data types from code content."""
        detected = set()
        
        for data_type, patterns in DATA_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.add(data_type)
                    break
        
        return list(detected) if detected else [DataClassification.INTERNAL]
    
    def _get_region(self, country_code: str) -> str:
        """Get region name for a country code."""
        if country_code in EEA_COUNTRIES:
            return "EEA"
        
        region_map = {
            "US": "North America", "CA": "North America", "MX": "North America",
            "GB": "Europe", "CH": "Europe", "NO": "Europe",
            "JP": "Asia Pacific", "KR": "Asia Pacific", "AU": "Asia Pacific",
            "SG": "Asia Pacific", "IN": "Asia Pacific", "CN": "Asia Pacific",
            "BR": "South America", "AR": "South America",
            "ZA": "Africa", "NG": "Africa",
            "AE": "Middle East", "IL": "Middle East", "BH": "Middle East",
        }
        
        return region_map.get(country_code, "Other")
    
    def _get_country_name(self, country_code: str) -> str:
        """Get country name from code."""
        names = {
            "US": "United States", "GB": "United Kingdom", "DE": "Germany",
            "FR": "France", "IE": "Ireland", "NL": "Netherlands",
            "SE": "Sweden", "IT": "Italy", "ES": "Spain",
            "JP": "Japan", "KR": "South Korea", "AU": "Australia",
            "SG": "Singapore", "IN": "India", "CN": "China",
            "BR": "Brazil", "CA": "Canada", "CH": "Switzerland",
            "BE": "Belgium", "FI": "Finland", "TW": "Taiwan",
            "HK": "Hong Kong", "ID": "Indonesia", "BH": "Bahrain",
            "ZA": "South Africa",
        }
        return names.get(country_code, country_code)
    
    async def _enrich_flows(self, flow_map: DataFlowMap) -> None:
        """Enrich flows with compliance information."""
        for flow in flow_map.flows:
            # Determine if cross-border
            is_cross_border = flow.source_country != flow.destination_country
            
            if is_cross_border:
                # Get applicable regulations
                flow.regulations = self._get_applicable_regulations(
                    flow.source_country,
                    flow.destination_country,
                )
                
                # Determine transfer mechanism needed
                flow.transfer_mechanism = self._get_transfer_mechanism(
                    flow.source_country,
                    flow.destination_country,
                )
                
                # Assess compliance status
                flow.compliance_status = self._assess_compliance(flow)
                
                # Assess risk level
                flow.risk_level = self._assess_risk(flow)
                
                # Determine required actions
                flow.actions_required = self._get_required_actions(flow)
    
    def _get_applicable_regulations(
        self,
        source_country: str,
        dest_country: str,
    ) -> list[str]:
        """Get regulations applicable to a cross-border transfer."""
        regulations = set()
        
        # Add source jurisdiction regulations
        if source_country in EEA_COUNTRIES:
            regulations.add("GDPR")
        source_regs = JURISDICTION_REGULATIONS.get(source_country, [])
        regulations.update(source_regs)
        
        # Add destination jurisdiction regulations
        if dest_country in EEA_COUNTRIES:
            regulations.add("GDPR")
        dest_regs = JURISDICTION_REGULATIONS.get(dest_country, [])
        regulations.update(dest_regs)
        
        return list(regulations)
    
    def _get_transfer_mechanism(
        self,
        source_country: str,
        dest_country: str,
    ) -> TransferMechanism:
        """Determine appropriate transfer mechanism."""
        # Within EEA - no mechanism needed
        if source_country in EEA_COUNTRIES and dest_country in EEA_COUNTRIES:
            return TransferMechanism.NONE
        
        # To adequate country
        if source_country in EEA_COUNTRIES and dest_country in EU_ADEQUATE_COUNTRIES:
            return TransferMechanism.ADEQUACY_DECISION
        
        # SCCs needed for most other cases
        if source_country in EEA_COUNTRIES:
            return TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES
        
        return TransferMechanism.NONE
    
    def _assess_compliance(self, flow: DataFlow) -> ComplianceStatus:
        """Assess compliance status of a flow."""
        # Check for data localization violations
        if flow.destination_country in DATA_LOCALIZATION_COUNTRIES:
            return ComplianceStatus.ACTION_REQUIRED
        
        # Check if mechanism is in place
        if flow.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
            return ComplianceStatus.NEEDS_REVIEW  # SCCs need to be verified
        
        if flow.transfer_mechanism == TransferMechanism.ADEQUACY_DECISION:
            return ComplianceStatus.COMPLIANT
        
        if flow.transfer_mechanism == TransferMechanism.NONE:
            if flow.source_country in EEA_COUNTRIES and flow.destination_country not in EEA_COUNTRIES:
                return ComplianceStatus.NON_COMPLIANT
        
        return ComplianceStatus.NEEDS_REVIEW
    
    def _assess_risk(self, flow: DataFlow) -> RiskLevel:
        """Assess risk level of a data flow."""
        risk_score = 0
        
        # Data sensitivity
        high_risk_data = [DataClassification.PHI, DataClassification.PCI, DataClassification.SENSITIVE]
        if any(dt in high_risk_data for dt in flow.data_types):
            risk_score += 3
        elif DataClassification.PII in flow.data_types:
            risk_score += 2
        
        # Destination risk
        from app.services.data_flow.models import HIGH_GOVERNMENT_ACCESS_RISK
        if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK:
            risk_score += 2
        
        # Data localization issues
        if flow.destination_country in DATA_LOCALIZATION_COUNTRIES:
            risk_score += 2
        
        # Missing transfer mechanism
        if flow.compliance_status == ComplianceStatus.NON_COMPLIANT:
            risk_score += 3
        
        # Map score to risk level
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _get_required_actions(self, flow: DataFlow) -> list[str]:
        """Get required actions for a flow."""
        actions = []
        
        if flow.compliance_status == ComplianceStatus.NON_COMPLIANT:
            actions.append("Implement appropriate transfer mechanism (SCCs or BCRs)")
        
        if flow.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
            actions.append("Execute Standard Contractual Clauses with data importer")
            actions.append("Complete Transfer Impact Assessment (TIA)")
        
        from app.services.data_flow.models import HIGH_GOVERNMENT_ACCESS_RISK
        if flow.destination_country in HIGH_GOVERNMENT_ACCESS_RISK:
            actions.append("Assess government access risk and implement supplementary measures")
            actions.append("Consider encryption with keys held in originating jurisdiction")
        
        if flow.destination_country in DATA_LOCALIZATION_COUNTRIES:
            actions.append(f"Review data localization requirements: {DATA_LOCALIZATION_COUNTRIES.get(flow.destination_country)}")
        
        if DataClassification.PII in flow.data_types:
            actions.append("Ensure data subject rights can be fulfilled")
        
        return actions
    
    def _calculate_statistics(self, flow_map: DataFlowMap) -> None:
        """Calculate summary statistics for the flow map."""
        flow_map.total_locations = len(flow_map.locations)
        flow_map.total_flows = len(flow_map.flows)
        
        flow_map.cross_border_flows = len([
            f for f in flow_map.flows
            if f.source_country != f.destination_country
        ])
        
        flow_map.compliant_flows = len([
            f for f in flow_map.flows
            if f.compliance_status == ComplianceStatus.COMPLIANT
        ])
        
        flow_map.action_required_flows = len([
            f for f in flow_map.flows
            if f.compliance_status in [ComplianceStatus.ACTION_REQUIRED, ComplianceStatus.NON_COMPLIANT]
        ])
        
        flow_map.critical_risks = len([f for f in flow_map.flows if f.risk_level == RiskLevel.CRITICAL])
        flow_map.high_risks = len([f for f in flow_map.flows if f.risk_level == RiskLevel.HIGH])
        flow_map.medium_risks = len([f for f in flow_map.flows if f.risk_level == RiskLevel.MEDIUM])
        flow_map.low_risks = len([f for f in flow_map.flows if f.risk_level == RiskLevel.LOW])
        
        flow_map.countries_involved = list(set(
            [l.country_code for l in flow_map.locations]
        ))
        flow_map.regions_involved = list(set(
            [l.region for l in flow_map.locations if l.region]
        ))
    
    async def get_flow_map(self, map_id: UUID) -> DataFlowMap | None:
        """Get a flow map by ID."""
        return self._flow_maps.get(map_id)
    
    async def add_flow(
        self,
        map_id: UUID,
        source_id: UUID,
        destination_id: UUID,
        data_types: list[str],
        purpose: str | None = None,
    ) -> DataFlow | None:
        """Add a manual flow to an existing map."""
        flow_map = self._flow_maps.get(map_id)
        if not flow_map:
            return None
        
        source = self._locations.get(source_id)
        destination = self._locations.get(destination_id)
        
        if not source or not destination:
            return None
        
        flow = DataFlow(
            name=f"{source.name} → {destination.name}",
            source_id=source.id,
            source_name=source.name,
            source_country=source.country_code,
            destination_id=destination.id,
            destination_name=destination.name,
            destination_country=destination.country_code,
            data_types=[DataClassification(dt) for dt in data_types],
            purpose=purpose,
            detected_from="manual",
        )
        
        flow_map.flows.append(flow)
        self._flows[flow.id] = flow
        
        # Re-enrich and recalculate
        await self._enrich_flows(flow_map)
        self._calculate_statistics(flow_map)
        
        return flow


# Singleton instance
_mapper_instance: DataFlowMapper | None = None


def get_data_flow_mapper() -> DataFlowMapper:
    """Get or create the data flow mapper singleton."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = DataFlowMapper()
    return _mapper_instance
