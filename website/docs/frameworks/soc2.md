---
sidebar_position: 7
title: SOC 2
description: Service Organization Control 2 compliance with ComplianceAgent
---

# SOC 2 Compliance

SOC 2 is an auditing framework for service organizations, based on the AICPA Trust Services Criteria.

## Overview

| Attribute | Value |
|-----------|-------|
| **Standard Body** | AICPA |
| **Applies To** | Service organizations |
| **Audit Type** | Third-party CPA audit |
| **Report Types** | Type I (point-in-time), Type II (period) |
| **Requirements Tracked** | 64 criteria |

## Trust Services Criteria

### Security (Required)

Protection against unauthorized access:

```yaml
security_criteria:
  CC1_control_environment:
    - integrity_and_ethical_values
    - board_oversight
    - organizational_structure
    - commitment_to_competence
    - accountability
  
  CC2_communication:
    - internal_communication
    - external_communication
  
  CC3_risk_assessment:
    - risk_identification
    - fraud_risk_assessment
    - change_management
  
  CC4_monitoring:
    - ongoing_evaluations
    - deficiency_communication
  
  CC5_control_activities:
    - selection_development_controls
    - technology_general_controls
    - policy_deployment
  
  CC6_logical_access:
    - access_provisioning
    - access_removal
    - infrastructure_access
    - vendor_access
  
  CC7_system_operations:
    - vulnerability_management
    - incident_detection
    - incident_response
    - recovery
  
  CC8_change_management:
    - change_authorization
    - change_testing
    - change_documentation
  
  CC9_risk_mitigation:
    - business_disruption
    - vendor_risk
```

### Availability (Optional)

System uptime and accessibility:

```python
class AvailabilityControls:
    """SOC 2 Availability criteria implementation."""
    
    # A1.1: Current capacity and projected needs
    async def capacity_management(self):
        return CapacityPlan(
            current_metrics=await self.get_current_metrics(),
            projections=await self.calculate_projections(),
            thresholds={
                "cpu": 80,
                "memory": 85,
                "storage": 90
            },
            alerts_configured=True
        )
    
    # A1.2: Environmental protections
    ENVIRONMENTAL_CONTROLS = {
        "fire_suppression": True,
        "climate_control": True,
        "power_redundancy": True,
        "flood_protection": True
    }
    
    # A1.3: Recovery and continuity
    async def disaster_recovery(self):
        return DRPlan(
            rpo_hours=4,  # Recovery Point Objective
            rto_hours=24, # Recovery Time Objective
            backup_frequency="hourly",
            dr_site="active",
            last_test_date=await self.get_last_dr_test()
        )
```

### Processing Integrity (Optional)

System processing is complete, valid, and timely:

```python
class ProcessingIntegrityControls:
    """SOC 2 Processing Integrity criteria."""
    
    # PI1.1: Processing objectives defined
    async def define_processing_slas(self):
        return ProcessingSLAs(
            completeness="99.99%",
            accuracy="99.99%",
            timeliness="within_sla",
            authorization="all_transactions"
        )
    
    # PI1.2: Input validation
    async def validate_input(self, data: Any) -> ValidationResult:
        return ValidationResult(
            schema_valid=await self.check_schema(data),
            business_rules=await self.check_business_rules(data),
            integrity_checks=await self.check_integrity(data)
        )
    
    # PI1.3: Processing monitoring
    async def monitor_processing(self):
        return ProcessingMonitor(
            completeness_checks=True,
            error_detection=True,
            reconciliation="daily",
            exception_handling=True
        )
```

### Confidentiality (Optional)

Protection of confidential information:

```python
class ConfidentialityControls:
    """SOC 2 Confidentiality criteria."""
    
    # C1.1: Identify confidential information
    CONFIDENTIAL_CATEGORIES = [
        "customer_data",
        "employee_data",
        "intellectual_property",
        "financial_data",
        "business_plans"
    ]
    
    # C1.2: Protect confidential information
    async def protect_confidential_data(self, data: ConfidentialData):
        return Protection(
            encryption_at_rest=await self.encrypt_storage(data),
            encryption_in_transit=True,
            access_control=await self.restrict_access(data),
            masking=await self.apply_masking(data)
        )
```

### Privacy (Optional)

Personal information handling:

```yaml
privacy_criteria:
  P1_notice:
    - privacy_notice_provided
    - purposes_disclosed
    - third_parties_identified
  
  P2_choice_consent:
    - consent_obtained
    - opt_out_available
  
  P3_collection:
    - collection_limitation
    - specified_purposes
  
  P4_use_retention_disposal:
    - purpose_limitation
    - retention_policy
    - secure_disposal
  
  P5_access:
    - access_provided
    - correction_available
  
  P6_disclosure:
    - third_party_disclosure_policy
    - contractual_protections
  
  P7_quality:
    - accuracy_maintained
    - completeness_verified
  
  P8_monitoring:
    - compliance_monitoring
    - incident_handling
```

## Control Implementation

### Access Control (CC6)

```python
class SOC2AccessControl:
    """SOC 2 CC6 - Logical and Physical Access Controls."""
    
    # CC6.1: Logical access security
    async def manage_access(self, user: User, resource: Resource):
        # Role-based access control
        if not self.rbac.permits(user.role, resource):
            raise AccessDenied()
        
        # Additional context checks
        if resource.sensitivity == "high":
            await self.require_mfa(user)
            await self.check_location(user)
        
        # Log access
        await self.audit_log.record(user, resource, "access")
    
    # CC6.2: User authentication
    AUTHENTICATION_REQUIREMENTS = {
        "password_policy": {
            "min_length": 12,
            "complexity": True,
            "rotation_days": 90
        },
        "mfa": {
            "required": True,
            "methods": ["totp", "hardware_key", "push"]
        },
        "session": {
            "timeout_minutes": 15,
            "single_session": False
        }
    }
    
    # CC6.3: User lifecycle
    async def onboard_user(self, user: NewUser):
        """Formal onboarding process."""
        # Approval workflow
        approval = await self.get_manager_approval(user)
        if not approval:
            raise OnboardingDenied()
        
        # Provision access
        await self.provision_access(user, user.role)
        
        # Security training
        await self.assign_training(user)
        
        # Document
        await self.audit_log.record("user_onboarded", user)
    
    async def offboard_user(self, user: User):
        """Formal offboarding process."""
        # Immediate access revocation
        await self.revoke_all_access(user)
        
        # Credential invalidation
        await self.invalidate_credentials(user)
        
        # Session termination
        await self.terminate_sessions(user)
        
        # Document
        await self.audit_log.record("user_offboarded", user)
```

### Change Management (CC8)

```python
class SOC2ChangeManagement:
    """SOC 2 CC8 - Change Management Controls."""
    
    async def process_change(self, change: ChangeRequest):
        # CC8.1: Change authorization
        await self.require_approval(change)
        
        # Development testing
        test_result = await self.run_tests(change)
        if not test_result.passed:
            raise ChangeRejected("Tests failed")
        
        # Security review
        security_review = await self.security_review(change)
        if security_review.has_issues:
            raise ChangeRejected(security_review.issues)
        
        # Deployment
        await self.deploy(change)
        
        # Verification
        await self.verify_deployment(change)
        
        # Documentation
        await self.document_change(change)
    
    CHANGE_MANAGEMENT_POLICY = {
        "approval_required": True,
        "testing_required": True,
        "rollback_plan": True,
        "documentation": True,
        "segregation_of_duties": True
    }
```

### Incident Response (CC7)

```python
class SOC2IncidentResponse:
    """SOC 2 CC7 - System Operations and Incident Response."""
    
    # CC7.3: Incident detection
    async def detect_incidents(self):
        return IncidentDetection(
            siem_enabled=True,
            log_correlation=True,
            anomaly_detection=True,
            alert_thresholds=self.alert_config
        )
    
    # CC7.4: Incident response
    async def respond_to_incident(self, incident: Incident):
        # Categorize and prioritize
        severity = await self.assess_severity(incident)
        
        # Contain
        await self.contain_incident(incident)
        
        # Investigate
        investigation = await self.investigate(incident)
        
        # Eradicate
        await self.eradicate_threat(incident, investigation)
        
        # Recover
        await self.recover_systems(incident)
        
        # Document
        await self.document_incident(incident, investigation)
        
        # Lessons learned
        await self.post_incident_review(incident)
    
    INCIDENT_RESPONSE_PLAN = {
        "categories": ["security", "availability", "data_breach"],
        "severity_levels": ["critical", "high", "medium", "low"],
        "escalation_matrix": True,
        "communication_plan": True,
        "regulatory_notification": True
    }
```

## Evidence Collection

ComplianceAgent automates evidence collection:

```python
class SOC2EvidenceCollector:
    """Automated evidence collection for SOC 2 audits."""
    
    async def collect_evidence(self, criteria: str) -> Evidence:
        collectors = {
            "CC6.1": self.collect_access_control_evidence,
            "CC6.2": self.collect_authentication_evidence,
            "CC6.3": self.collect_access_provisioning_evidence,
            "CC7.1": self.collect_vulnerability_evidence,
            "CC7.2": self.collect_monitoring_evidence,
            "CC8.1": self.collect_change_management_evidence,
        }
        
        return await collectors[criteria]()
    
    async def collect_access_control_evidence(self) -> Evidence:
        return Evidence(
            criteria="CC6.1",
            artifacts=[
                await self.get_rbac_configuration(),
                await self.get_access_reviews(),
                await self.get_access_logs(),
                await self.get_access_policy()
            ]
        )
```

## Common Gaps

### 1. Missing Access Reviews

**Issue:** No periodic access reviews documented.

**Solution:**

```python
async def conduct_access_review():
    """Quarterly access review per CC6.3."""
    users = await get_all_users()
    
    for user in users:
        review = AccessReview(
            user=user,
            current_access=await get_user_access(user),
            reviewer=user.manager,
            date=datetime.now()
        )
        
        # Send to manager for review
        await send_review_request(review)
        
        # Document
        await store_review(review)
```

### 2. Incomplete Change Documentation

**Issue:** Changes deployed without full documentation.

**Solution:**

```yaml
# Required change documentation
change_record:
  required_fields:
    - change_id
    - description
    - requester
    - approver
    - approval_date
    - test_results
    - deployment_date
    - verification_results
    - rollback_plan
```

### 3. No Incident Response Testing

**Issue:** IRP exists but never tested.

**Solution:**

```python
async def test_incident_response():
    """Annual incident response test per CC7.4."""
    # Tabletop exercise
    scenario = IncidentScenario(
        type="ransomware",
        affected_systems=["payment_processing"],
        discovery_method="user_report"
    )
    
    # Execute response procedures
    response = await execute_irp_test(scenario)
    
    # Document results
    await document_irp_test(response)
    
    # Update IRP based on learnings
    await update_irp(response.lessons_learned)
```

## Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  soc2:
    enabled: true
    
    # Report type
    report_type: "type_ii"
    
    # Trust services criteria
    criteria:
      security: true       # Required
      availability: true
      processing_integrity: false
      confidentiality: true
      privacy: false
    
    # Audit period
    audit_period:
      start: "2024-01-01"
      end: "2024-12-31"
```

## Templates

| Template | Description |
|----------|-------------|
| `soc2-access-review` | Quarterly access review workflow |
| `soc2-change-management` | Change management process |
| `soc2-incident-response` | Incident response procedures |
| `soc2-evidence-collection` | Automated evidence gathering |

---

See also: [PCI-DSS](./pci-dss) | [HIPAA](./hipaa) | [Audit Trails](../guides/audit-trails)
