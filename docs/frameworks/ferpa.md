# FERPA Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with the Family Educational Rights and Privacy Act (FERPA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Family Educational Rights and Privacy Act |
| **Jurisdiction** | United States |
| **Effective Date** | 1974 (amended multiple times) |
| **Enforcing Authority** | U.S. Department of Education |
| **Applies To** | Educational institutions receiving federal funding |
| **Penalty** | Loss of federal funding |

## Key Concepts

### Education Records

Records directly related to a student maintained by an educational institution:

| Included | Excluded |
|----------|----------|
| Grades and transcripts | Sole possession records |
| Student schedules | Law enforcement records |
| Financial aid records | Employment records (non-student) |
| Disciplinary records | Medical/treatment records |
| Enrollment information | Alumni records (post-attendance) |

### Directory Information

Information that may be disclosed without consent (if properly designated):

- Name, address, telephone, email
- Date and place of birth
- Major field of study
- Enrollment status
- Degrees and awards received
- Participation in activities/sports

## Key Requirements

### Parent/Student Rights

| Right | Description | Implementation |
|-------|-------------|----------------|
| **Inspect Records** | View education records within 45 days | Record access portal |
| **Request Amendment** | Correct inaccurate records | Edit request workflow |
| **Consent to Disclosure** | Control who sees records | Consent management |
| **File Complaints** | Report violations to DOE | Audit trail |

### Institution Obligations

| Obligation | Description | Code Impact |
|------------|-------------|-------------|
| **Annual Notification** | Inform students of FERPA rights | Notification system |
| **Access Controls** | Limit access to authorized personnel | RBAC implementation |
| **Disclosure Logging** | Track all record disclosures | Audit logging |
| **Consent Management** | Obtain consent before disclosure | Consent workflow |
| **Directory Information Opt-Out** | Allow students to restrict directory info | Preference management |

## Legitimate Educational Interest

Access without consent is permitted when:

1. School official has legitimate educational interest
2. Disclosure is to another school (enrollment)
3. Disclosure is for financial aid purposes
4. Disclosure is for accreditation purposes
5. Disclosure is for health/safety emergencies
6. Disclosure is pursuant to court order (with notice)

## ComplianceAgent Detection

### Automatically Detected Issues

```
FERPA-001: Education records accessible without authentication
FERPA-002: Missing access logging for student records
FERPA-003: No consent verification before disclosure
FERPA-004: Insufficient access controls on student data
FERPA-005: Directory information shared without opt-out check
FERPA-006: Student records retained beyond policy period
FERPA-007: Third-party access without data sharing agreement
FERPA-008: Missing audit trail for record amendments
FERPA-009: Inadequate data classification for education records
FERPA-010: Cross-system data sharing without controls
```

### Example Detection

**Issue: FERPA-001 - Unsecured education records**

```python
# ❌ Non-compliant: No authentication or authorization
@app.get("/api/students/{student_id}/grades")
async def get_student_grades(student_id: str):
    # Anyone can access student grades
    return await db.grades.get_by_student(student_id)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Proper access controls and logging
from complianceagent import audit_log, require_role

@app.get("/api/students/{student_id}/grades")
@require_authentication
@require_role(["instructor", "registrar", "advisor"])
@audit_log(action="education_record_access", regulation="FERPA")
async def get_student_grades(
    student_id: str,
    current_user: User = Depends(get_current_user),
):
    # FERPA: Verify legitimate educational interest
    if not await has_legitimate_interest(current_user, student_id):
        raise ForbiddenException(
            "Access denied: No legitimate educational interest"
        )
    
    # FERPA: Log the disclosure
    await log_record_access(
        record_type="grades",
        student_id=student_id,
        accessor_id=current_user.id,
        purpose="legitimate_educational_interest",
    )
    
    return await db.grades.get_by_student(student_id)
```

**Issue: FERPA-005 - Directory information without opt-out check**

```python
# ❌ Non-compliant: No opt-out verification
@app.get("/api/directory")
async def get_student_directory():
    # Returns all students without checking opt-out preferences
    students = await db.students.all()
    return [{"name": s.name, "email": s.email, "major": s.major} for s in students]
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Respect directory information opt-out
@app.get("/api/directory")
@require_authentication
async def get_student_directory():
    # FERPA: Only include students who haven't opted out
    students = await db.students.filter(
        directory_opt_out=False,
        enrollment_status="active"
    )
    
    return [
        {
            "name": s.name,
            "email": s.email if not s.email_restricted else None,
            "major": s.major if not s.major_restricted else None,
        }
        for s in students
    ]

# Student can opt out of directory information
@app.post("/api/students/{student_id}/directory-opt-out")
@require_authentication
async def opt_out_directory(
    student_id: str,
    opt_out: DirectoryOptOut,
    current_user: User = Depends(get_current_user),
):
    # Only the student themselves can opt out
    if current_user.student_id != student_id:
        raise ForbiddenException("Can only modify your own preferences")
    
    await db.students.update(
        student_id,
        directory_opt_out=opt_out.full_opt_out,
        email_restricted=opt_out.restrict_email,
        major_restricted=opt_out.restrict_major,
    )
    
    await audit_log(
        action="directory_opt_out_changed",
        student_id=student_id,
        changes=opt_out.dict(),
    )
    
    return {"status": "preferences_updated"}
```

**Issue: FERPA-007 - Third-party sharing without agreement**

```python
# ❌ Non-compliant: Sharing with third party without controls
@app.post("/api/integrations/lms/sync")
async def sync_to_lms(course_id: str):
    students = await db.enrollments.get_by_course(course_id)
    # Sending student data to external LMS without verification
    await external_lms.sync_students(students)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Third-party sharing with proper controls
@app.post("/api/integrations/lms/sync")
@require_role(["system_admin"])
@audit_log(action="third_party_disclosure", regulation="FERPA")
async def sync_to_lms(
    course_id: str,
    current_user: User = Depends(get_current_user),
):
    # FERPA: Verify data sharing agreement exists
    integration = await db.integrations.get("lms")
    if not integration.has_valid_agreement:
        raise ForbiddenException(
            "Cannot share data: No valid data sharing agreement"
        )
    
    students = await db.enrollments.get_by_course(course_id)
    
    # FERPA: Only share minimum necessary data
    safe_data = [
        {
            "student_id": s.external_id,  # Not internal ID
            "name": s.name,
            "email": s.edu_email,
            "enrollment_status": s.status,
        }
        for s in students
        # Exclude students who opted out of third-party sharing
        if not s.third_party_opt_out
    ]
    
    # Log the disclosure
    await log_disclosure(
        disclosure_type="third_party",
        recipient="lms_provider",
        record_count=len(safe_data),
        purpose="educational_service",
        agreement_id=integration.agreement_id,
    )
    
    await external_lms.sync_students(safe_data)
    return {"synced": len(safe_data)}
```

## Data Model Recommendations

```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID, primary_key=True)
    student_id = Column(String, unique=True)  # External ID
    
    # Directory information (may be disclosed if not opted out)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    major = Column(String)
    enrollment_status = Column(String)
    
    # FERPA: Opt-out preferences
    directory_opt_out = Column(Boolean, default=False)
    email_restricted = Column(Boolean, default=False)
    phone_restricted = Column(Boolean, default=False)
    third_party_opt_out = Column(Boolean, default=False)
    
    # Relationships
    education_records = relationship("EducationRecord", back_populates="student")
    consents = relationship("FERPAConsent", back_populates="student")


class EducationRecord(Base):
    __tablename__ = "education_records"
    
    id = Column(UUID, primary_key=True)
    student_id = Column(UUID, ForeignKey("students.id"))
    record_type = Column(String)  # grades, transcript, disciplinary, etc.
    content = Column(JSON)  # Encrypted at rest
    created_at = Column(DateTime)
    
    # FERPA: Access tracking
    access_logs = relationship("RecordAccessLog", back_populates="record")


class RecordAccessLog(Base):
    """FERPA-required disclosure log."""
    __tablename__ = "record_access_logs"
    
    id = Column(UUID, primary_key=True)
    record_id = Column(UUID, ForeignKey("education_records.id"))
    accessor_id = Column(UUID, ForeignKey("users.id"))
    access_time = Column(DateTime)
    purpose = Column(String)  # legitimate_interest, consent, subpoena, etc.
    consent_id = Column(UUID, ForeignKey("ferpa_consents.id"), nullable=True)
```

## SDK Integration

```python
from complianceagent import configure, ferpa_protected, audit_log

configure(regulations=["FERPA"])

# Protect education record access
@ferpa_protected(record_type="grades")
async def get_grades(student_id: str, accessor: User):
    return await db.grades.get(student_id)

# Consent-based disclosure
@ferpa_consent_required(purpose="transfer_records")
async def send_transcript(student_id: str, recipient_school: str):
    transcript = await db.transcripts.get(student_id)
    await send_to_school(recipient_school, transcript)

# Directory information with opt-out check
@ferpa_directory_check
async def get_student_info(student_id: str):
    return await db.students.get_directory_info(student_id)
```

## Compliance Dashboard

```
Dashboard → Compliance → FERPA

┌─────────────────────────────────────────────────────────┐
│ FERPA Compliance Status                                 │
├─────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Compliant                            │
│                                                         │
│ Access Controls:           ✅ 47/47 endpoints secured   │
│ Audit Logging:             ✅ 100% coverage            │
│ Consent Management:        ✅ Active                   │
│ Directory Opt-Out:         ✅ 234 students opted out   │
│ Record Amendment Requests: ⚠️  3 pending               │
│                                                         │
│ Last 30 Days:                                          │
│   - Record accesses: 12,456                            │
│   - Disclosures logged: 89                             │
│   - Consent-based shares: 23                           │
│   - Amendment requests: 7                              │
└─────────────────────────────────────────────────────────┘
```

## Annual Notification Template

```markdown
# Annual FERPA Notification

[Institution Name] maintains education records in accordance with the 
Family Educational Rights and Privacy Act (FERPA).

## Your Rights Under FERPA

1. **Inspect and Review**: You may inspect your education records within 
   45 days of submitting a request.

2. **Request Amendment**: You may request correction of records you 
   believe are inaccurate or misleading.

3. **Consent to Disclosure**: With limited exceptions, your consent is 
   required before disclosing personally identifiable information.

4. **File a Complaint**: You may file a complaint with the U.S. 
   Department of Education.

## Directory Information

We designate the following as directory information:
- Name, address, telephone number, email
- Date and place of birth
- Major field of study
- Enrollment status
- Degrees and awards received

To opt out of directory information disclosure, visit [Portal URL] 
or submit the Directory Information Opt-Out Form by [Date].

## Questions

Contact the Registrar's Office at registrar@institution.edu
```

## Resources

- [FERPA Regulations (34 CFR Part 99)](https://www.ecfr.gov/current/title-34/part-99)
- [DOE FERPA Guidance](https://studentprivacy.ed.gov/)
- [PTAC Best Practices](https://studentprivacy.ed.gov/resources)

## Related Documentation

- [GDPR Compliance](gdpr.md) - For international student data
- [Security Best Practices](../guides/security.md)
- [Audit Trail Feature](../features/audit-trail.md)
