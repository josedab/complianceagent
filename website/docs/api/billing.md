---
sidebar_position: 7
title: Billing API
description: API endpoints for subscription and usage management
---

# Billing API

Manage subscriptions, view usage, and access invoices.

## Get Current Subscription

```bash
GET /api/v1/billing/subscription
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "sub_abc123",
    "plan": {
      "id": "pro",
      "name": "Pro",
      "price_monthly": 99,
      "currency": "USD"
    },
    "status": "active",
    "current_period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "billing_cycle": "monthly",
    "payment_method": {
      "type": "card",
      "last4": "4242",
      "brand": "visa",
      "exp_month": 12,
      "exp_year": 2025
    },
    "features": {
      "repositories": 25,
      "frameworks": "unlimited",
      "api_calls_per_month": 50000,
      "audit_retention_days": 730,
      "team_members": 10
    },
    "created_at": "2023-06-15T00:00:00Z"
  }
}
```

## Get Usage

```bash
GET /api/v1/billing/usage
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | Billing period: `current`, `previous`, or `YYYY-MM` |

### Response

```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "usage": {
      "repositories": {
        "used": 18,
        "limit": 25,
        "percentage": 72
      },
      "api_calls": {
        "used": 32450,
        "limit": 50000,
        "percentage": 65
      },
      "scans": {
        "used": 542,
        "limit": null,
        "percentage": null
      },
      "fixes_generated": {
        "used": 89,
        "limit": null,
        "percentage": null
      },
      "storage_gb": {
        "used": 4.2,
        "limit": 50,
        "percentage": 8
      }
    },
    "overage": {
      "api_calls": 0,
      "cost": 0
    }
  }
}
```

## Get Usage History

```bash
GET /api/v1/billing/usage/history
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | date | Start date (YYYY-MM) |
| `to` | date | End date (YYYY-MM) |

### Response

```json
{
  "success": true,
  "data": {
    "periods": [
      {
        "period": "2024-01",
        "api_calls": 32450,
        "scans": 542,
        "fixes_generated": 89,
        "repositories_active": 18
      },
      {
        "period": "2023-12",
        "api_calls": 28930,
        "scans": 487,
        "fixes_generated": 72,
        "repositories_active": 16
      }
    ]
  }
}
```

## List Plans

```bash
GET /api/v1/billing/plans
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "free",
      "name": "Free",
      "price_monthly": 0,
      "price_yearly": 0,
      "currency": "USD",
      "features": {
        "repositories": 3,
        "frameworks": 2,
        "api_calls_per_month": 1000,
        "audit_retention_days": 30,
        "team_members": 1
      },
      "highlights": [
        "3 repositories",
        "2 frameworks",
        "Basic scanning"
      ]
    },
    {
      "id": "pro",
      "name": "Pro",
      "price_monthly": 99,
      "price_yearly": 990,
      "currency": "USD",
      "features": {
        "repositories": 25,
        "frameworks": "unlimited",
        "api_calls_per_month": 50000,
        "audit_retention_days": 730,
        "team_members": 10
      },
      "highlights": [
        "25 repositories",
        "All frameworks",
        "AI-powered fixes",
        "Priority support"
      ]
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "price_monthly": null,
      "price_yearly": null,
      "currency": "USD",
      "contact_sales": true,
      "features": {
        "repositories": "unlimited",
        "frameworks": "unlimited",
        "api_calls_per_month": "unlimited",
        "audit_retention_days": 2555,
        "team_members": "unlimited"
      },
      "highlights": [
        "Unlimited everything",
        "SSO/SAML",
        "Dedicated support",
        "SLA guarantee",
        "Custom integrations"
      ]
    }
  ]
}
```

## Update Subscription

```bash
POST /api/v1/billing/subscription
```

### Request Body

```json
{
  "plan_id": "pro",
  "billing_cycle": "yearly"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "subscription_id": "sub_abc123",
    "plan_id": "pro",
    "status": "active",
    "effective_date": "2024-02-01T00:00:00Z",
    "prorated_amount": 45.50,
    "next_invoice": {
      "amount": 990,
      "date": "2024-02-01T00:00:00Z"
    }
  }
}
```

## Cancel Subscription

```bash
DELETE /api/v1/billing/subscription
```

### Request Body

```json
{
  "reason": "switching_to_competitor",
  "feedback": "Missing framework support",
  "cancel_at_period_end": true
}
```

### Response

```json
{
  "success": true,
  "data": {
    "subscription_id": "sub_abc123",
    "status": "canceled",
    "cancel_at": "2024-01-31T23:59:59Z",
    "access_until": "2024-01-31T23:59:59Z"
  }
}
```

## List Invoices

```bash
GET /api/v1/billing/invoices
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `paid`, `pending`, `failed` |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "inv_abc123",
      "number": "INV-2024-0001",
      "status": "paid",
      "amount": 99.00,
      "currency": "USD",
      "period": {
        "start": "2024-01-01",
        "end": "2024-01-31"
      },
      "line_items": [
        {
          "description": "Pro Plan - January 2024",
          "amount": 99.00
        }
      ],
      "paid_at": "2024-01-01T00:00:00Z",
      "pdf_url": "https://billing.complianceagent.io/invoices/inv_abc123.pdf",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 12
  }
}
```

## Get Invoice

```bash
GET /api/v1/billing/invoices/{invoice_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "inv_abc123",
    "number": "INV-2024-0001",
    "status": "paid",
    "amount": 99.00,
    "tax": 0,
    "total": 99.00,
    "currency": "USD",
    "billing_address": {
      "company": "Acme Corp",
      "address": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "postal_code": "94105",
      "country": "US"
    },
    "line_items": [
      {
        "description": "Pro Plan - January 2024",
        "quantity": 1,
        "unit_price": 99.00,
        "amount": 99.00
      }
    ],
    "payment": {
      "method": "card",
      "last4": "4242",
      "brand": "visa"
    },
    "paid_at": "2024-01-01T00:00:00Z",
    "pdf_url": "https://billing.complianceagent.io/invoices/inv_abc123.pdf"
  }
}
```

## Update Payment Method

```bash
POST /api/v1/billing/payment-method
```

### Request Body

```json
{
  "payment_method_id": "pm_xyz789"
}
```

:::note
Use Stripe.js to collect payment details securely and obtain a `payment_method_id`.
:::

### Response

```json
{
  "success": true,
  "data": {
    "payment_method": {
      "id": "pm_xyz789",
      "type": "card",
      "last4": "1234",
      "brand": "mastercard",
      "exp_month": 6,
      "exp_year": 2026
    }
  }
}
```

## Get Billing Portal URL

```bash
POST /api/v1/billing/portal
```

### Request Body

```json
{
  "return_url": "https://your-app.com/settings/billing"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "url": "https://billing.stripe.com/session/abc123",
    "expires_at": "2024-01-15T11:00:00Z"
  }
}
```

## Update Billing Information

```bash
PATCH /api/v1/billing/info
```

### Request Body

```json
{
  "company_name": "Acme Corporation",
  "email": "billing@acme.com",
  "address": {
    "line1": "123 Main St",
    "line2": "Suite 100",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US"
  },
  "tax_id": "US123456789"
}
```

## Get Billing Alerts

```bash
GET /api/v1/billing/alerts
```

### Response

```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "type": "usage_warning",
        "message": "API usage at 80% of monthly limit",
        "threshold": 80,
        "current": 82,
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

## Configure Billing Alerts

```bash
POST /api/v1/billing/alerts
```

### Request Body

```json
{
  "alerts": [
    {
      "metric": "api_calls",
      "threshold_percent": 80,
      "notification_channels": ["email", "slack"]
    },
    {
      "metric": "repositories",
      "threshold_percent": 90,
      "notification_channels": ["email"]
    }
  ]
}
```

---

See also: [API Overview](./overview) | [Authentication](./authentication)
