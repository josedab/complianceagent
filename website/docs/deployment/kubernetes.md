---
sidebar_position: 3
title: Kubernetes Deployment
description: Deploy ComplianceAgent on Kubernetes
---

# Kubernetes Deployment

Deploy ComplianceAgent on any Kubernetes cluster for maximum flexibility and scale.

## Prerequisites

- Kubernetes 1.28+
- kubectl configured
- Helm 3.12+
- Ingress controller (nginx, traefik, etc.)
- cert-manager (for TLS)

## Quick Start with Helm

```bash
# Add ComplianceAgent Helm repository
helm repo add complianceagent https://charts.complianceagent.io
helm repo update

# Install with default values
helm install complianceagent complianceagent/complianceagent \
  --namespace complianceagent \
  --create-namespace

# Or with custom values
helm install complianceagent complianceagent/complianceagent \
  --namespace complianceagent \
  --create-namespace \
  -f values.yaml
```

## Architecture

```yaml
                    ┌─────────────────────────────────────────────────────┐
                    │                 Kubernetes Cluster                   │
                    │                                                      │
┌──────────┐        │  ┌─────────────┐                                    │
│  Users   │───────▶│  │   Ingress   │                                    │
└──────────┘        │  │  Controller │                                    │
                    │  └──────┬──────┘                                    │
                    │         │                                           │
                    │         ▼                                           │
                    │  ┌─────────────┐     ┌─────────────┐               │
                    │  │  Frontend   │     │   Backend   │               │
                    │  │   Service   │     │   Service   │               │
                    │  │             │     │             │               │
                    │  │ ┌─────────┐ │     │ ┌─────────┐ │               │
                    │  │ │  Pod x3 │ │     │ │  Pod x3 │ │               │
                    │  │ └─────────┘ │     │ └─────────┘ │               │
                    │  └─────────────┘     └──────┬──────┘               │
                    │                             │                       │
                    │  ┌──────────────────────────┼────────────────────┐ │
                    │  │    StatefulSets / External Services          │ │
                    │  │                          │                    │ │
                    │  │  ┌───────────┐   ┌───────┴─────┐   ┌────────┐ │ │
                    │  │  │ PostgreSQL│   │    Redis    │   │  ES    │ │ │
                    │  │  │           │   │             │   │        │ │ │
                    │  │  └───────────┘   └─────────────┘   └────────┘ │ │
                    │  └──────────────────────────────────────────────┘ │
                    │                                                    │
                    └────────────────────────────────────────────────────┘
```

## Helm Values

```yaml
# values.yaml
global:
  environment: production
  domain: compliance.example.com

# Frontend configuration
frontend:
  replicaCount: 3
  image:
    repository: ghcr.io/complianceagent/frontend
    tag: latest
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Backend configuration
backend:
  replicaCount: 3
  image:
    repository: ghcr.io/complianceagent/backend
    tag: latest
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
  
  env:
    WORKERS: "4"
    LOG_LEVEL: "info"

# Worker configuration
worker:
  replicaCount: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

# PostgreSQL
postgresql:
  enabled: true
  auth:
    database: complianceagent
    username: complianceagent
    existingSecret: complianceagent-db-secret
  primary:
    persistence:
      size: 100Gi
      storageClass: fast-ssd
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
  metrics:
    enabled: true

# Redis
redis:
  enabled: true
  architecture: replication
  auth:
    existingSecret: complianceagent-redis-secret
  master:
    persistence:
      size: 10Gi
  replica:
    replicaCount: 2

# Elasticsearch
elasticsearch:
  enabled: true
  replicas: 3
  volumeClaimTemplate:
    resources:
      requests:
        storage: 100Gi

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
  hosts:
    - host: compliance.example.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: backend
  tls:
    - secretName: complianceagent-tls
      hosts:
        - compliance.example.com

# Secrets (use external secrets operator in production)
secrets:
  create: false
  externalSecrets:
    enabled: true
    secretStore: vault
```

## Manual Kubernetes Manifests

### Namespace and Secrets

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: complianceagent
  labels:
    name: complianceagent

---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: complianceagent-secrets
  namespace: complianceagent
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  DATABASE_URL: "postgresql://user:pass@postgres:5432/complianceagent"
  REDIS_URL: "redis://redis:6379/0"
  GITHUB_TOKEN: "ghp_xxxxxxxxxxxx"
```

### Backend Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: complianceagent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: ghcr.io/complianceagent/backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: complianceagent-secrets
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true

---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: complianceagent
spec:
  selector:
    app: backend
  ports:
    - port: 8000
      targetPort: 8000
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: complianceagent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

### Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
  namespace: complianceagent
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: backend
```

### Network Policy

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: complianceagent
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
        - podSelector:
            matchLabels:
              app: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

## External Secrets

For production, use External Secrets Operator with your secrets manager:

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: complianceagent-secrets
  namespace: complianceagent
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: complianceagent-secrets
  data:
    - secretKey: SECRET_KEY
      remoteRef:
        key: complianceagent/production
        property: secret_key
    - secretKey: GITHUB_TOKEN
      remoteRef:
        key: complianceagent/production
        property: github_token
```

## Monitoring with Prometheus

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: complianceagent
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
```

## Operations

### Rolling Update

```bash
# Update image
kubectl set image deployment/backend \
  backend=ghcr.io/complianceagent/backend:v1.2.3 \
  -n complianceagent

# Watch rollout
kubectl rollout status deployment/backend -n complianceagent
```

### Rollback

```bash
# View history
kubectl rollout history deployment/backend -n complianceagent

# Rollback to previous
kubectl rollout undo deployment/backend -n complianceagent

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n complianceagent
```

### Database Migration

```bash
# Run as a Job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: complianceagent
spec:
  template:
    spec:
      containers:
        - name: migration
          image: ghcr.io/complianceagent/backend:latest
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - secretRef:
                name: complianceagent-secrets
      restartPolicy: Never
  backoffLimit: 3
EOF
```

---

See also: [Docker Deployment](./docker) | [AWS Deployment](./aws)
