---
sidebar_label: Kubernetes
tags: 
- deployment
- kubernetes
- helm
---

# Kubernetes Deployment Guide

This guide provides instructions for deploying the Doubleword
Control Layer to Kubernetes using Helm.

After following this guide, you'll have a production-ready AI model management
platform running in your Kubernetes cluster with secure TLS encryption and
SSO authentication.

Kubernetes deployment is ideal for organizations requiring high availability,
automatic scaling, and integration with existing Kubernetes infrastructure. For
simpler single-server deployments, see our [Docker Compose deployment
guide](./1-docker-compose.md).

## Prerequisites

Before beginning your deployment, ensure you have the necessary infrastructure
and credentials prepared.

### System Requirements

Your Kubernetes cluster must be running version 1.24 or later with kubectl
configured to access your target cluster. You'll also need Helm 3.8 or later
installed for managing the deployment.

### OAuth Provider Configuration

The Control Layer integrates with OIDC providers for user authentication.
You can use any compliant provider such as Google Workspace, Microsoft Azure
AD, Okta, or similar enterprise identity services.

Create a new OAuth application in your provider's administrative console.
Configure the redirect URI to match your deployment domain followed by `/auth`.
For example, if deploying at `https://ai.company.com`, set the redirect URI to
`https://ai.company.com/auth`. Record the Client ID and Client Secret generated
by your provider, as these credentials are required for the Helm configuration.

Ensure your OAuth provider allows the appropriate users to access the
application.

## Installing the Helm Chart

The Control Layer Helm chart is distributed through GitHub Container Registry
as an OCI artifact. First, create a dedicated namespace for your deployment:

```bash
kubectl create namespace control-layer
```

Install the chart directly from the OCI registry (this will require you to
authenticate. Contact your account manager if you don't have access):

```bash
helm install control-layer oci://ghcr.io/doublewordai/control-layer/control-layer \
  --namespace control-layer \
  --values values.yaml
```

## Configuration with Values

Create a `values.yaml` file to customize your deployment. This file contains
the essential configuration for your Control Layer installation.

```yaml
# OAuth Configuration
secrets:
  oauth:
    create: true
    data:
      CLIENT_ID: "your-oauth-client-id"
      CLIENT_SECRET: "your-oauth-client-secret"
      PROVIDER: "google"  # Options: google, microsoft, oidc, github, okta
      AUTH_URL: "https://accounts.google.com/o/oauth2/v2/auth"
      TOKEN_URL: "https://oauth2.googleapis.com/token"
      FQDN: "your-production-domain.com"
      JWT_SECRET: "generate-secure-random-string-minimum-32-characters"
      ALLOW_ALL_USERS: "false"  # Set to "true" to allow any authenticated user

# Ingress Configuration
ssoProxy:
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: your-production-domain.com
        paths:
          - path: /
            pathType: Prefix
            port: 80
    tls:
      - secretName: control-layer-tls
        hosts:
          - your-production-domain.com
```

Replace all placeholder values with your actual configuration details. Generate
cryptographically secure random strings for the JWT secret using a tool like
`openssl rand -base64 32`.

For OAuth provider configuration, adjust the AUTH_URL and TOKEN_URL based on
your chosen provider. Common configurations include:

**Google OAuth:**

- PROVIDER: `google`
- AUTH_URL: `https://accounts.google.com/o/oauth2/v2/auth`
- TOKEN_URL: `https://oauth2.googleapis.com/token`

**Microsoft Azure AD:**

- PROVIDER: `microsoft`
- AUTH_URL: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize`
- TOKEN_URL: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`

**Generic OIDC Provider:**

- PROVIDER: `oidc`
- AUTH_URL: `https://your-provider.com/authorize`
- TOKEN_URL: `https://your-provider.com/token`
- USER_INFO_URL: `https://your-provider.com/userinfo`

## TLS Certificate Configuration

The Doubleword Control Layer must be served with TLS for secure operation. You
can configure TLS termination in two ways depending on your infrastructure
requirements and security policies.

### TLS Termination at Ingress with cert-manager (Recommended)

For automatic certificate management, we recommend using cert-manager with
Let's Encrypt. This approach handles certificate issuance and renewal
automatically.

To set this up for the nginx ingress controller, see the guide
[here](https://cert-manager.io/docs/tutorials/acme/nginx-ingress/).

This configuration automatically provisions and renews TLS certificates from
Let's Encrypt. The certificates are stored in the secret specified in the
ingress TLS configuration.

Since TLS will be terminated at the ingress controller, ensure TLS termination is disabled in the nginx service:

```yaml
ssoProxy:
  nginx:
    tls:
      enabled: false  # Disable nginx TLS when using ingress
  ingress:
    enabled: true
```

### TLS Termination in the included Nginx server

For environments where you want to manage certificates manually or use existing
certificates, and you don't want to configure termination at the cluster
ingress, you can configure the provided nginx to handle TLS termination.

Create a Kubernetes secret with your certificate files:

```bash
kubectl create secret tls control-layer-tls \
  --cert=/path/to/your/fullchain.pem \
  --key=/path/to/your/privkey.pem \
  --namespace control-layer
```

Then configure your values.yaml to use nginx for TLS termination:

```yaml
ssoProxy:
  nginx:
    tls:
      enabled: true
      secretName: control-layer-tls
  ingress:
    enabled: false  # Disable ingress when using nginx TLS
```

## Deploying the Application

With your configuration ready, deploy or update the Control Layer installation:

```bash
helm upgrade --install control-layer \
  oci://ghcr.io/doublewordai/control-layer/control-layer \
  --namespace control-layer \
  --values values.yaml \
  --wait
```

The `--wait` flag ensures Helm waits for all resources to be ready before
completing. Monitor the deployment progress:

```bash
kubectl get pods -n control-layer -w
```

All pods should reach the Running state within a minute or so. If any pods fail
to start, check their logs:

```bash
kubectl logs -n control-layer deployment/clay
kubectl logs -n control-layer deployment/sso-proxy

