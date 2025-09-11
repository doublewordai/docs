--- 
sidebar_label: Docker Compose
tags: 
- deployment
- docker
- docker-compose
---

# Docker Compose Deployment Guide

This guide provides comprehensive instructions for deploying the Doubleword
Control Layer using Docker Compose.

After following this guide, you'll have a
production-ready AI model management platform running with secure TLS
encryption and OAuth authentication.

Docker compose works great when deploying the control layer on a single server.
If you would like to go beyond, check out our [kubernetes deployment
guide](./2-kubernetes.md).

## Prerequisites

Before beginning your deployment, ensure you have the necessary infrastructure
and credentials prepared.

### System Requirements

Your deployment environment must have Docker and Docker Compose installed and
running.

### OAuth Provider Configuration

The Control Layer integrates with OAuth 2.0 providers for user authentication.
You can use any compliant provider such as Google Workspace, Microsoft Azure
AD, Okta, Auth0, or similar enterprise identity services.

Create a new OAuth application in your provider's administrative console.
Configure the redirect URI to match your deployment domain followed by `/auth`.
For example, if deploying at `https://ai.company.com`, set the redirect URI to
`https://ai.company.com/auth`. Record the Client ID and Client Secret generated
by your provider, as these credentials are required for the environment
configuration.

Ensure your OAuth provider allows the appropriate users to access the
application. The first user to successfully authenticate will automatically
receive administrator privileges in the Control Layer system.

## Getting the Deployment Files

Start by obtaining the Control Layer deployment files from the official GitHub
repository. These files contain the Docker Compose configuration and all
necessary service definitions.

```bash
git clone https://github.com/doublewordai/control-layer.git 
cd control-layer 
```

The repository includes production-ready Docker Compose files that orchestrate
all required services including the Clay API server, Dashboard web interface,
authentication proxy, and PostgreSQL database.

## Environment Configuration

Create a production environment configuration file named `.env` in the
repository root directory. This file contains all environment variables
required by the Control Layer services.

```bash
# Domain Configuration
FQDN=your-production-domain.com

# OAuth Provider Configuration
PROVIDER=google  # Options: google, microsoft, oidc, github, okta
CLIENT_ID=your-oauth-client-id-from-provider
CLIENT_SECRET=your-oauth-client-secret-from-provider

# OAuth Endpoints (adjust based on your provider)
AUTH_URL= # i.e. https://accounts.google.com/o/oauth2/v2/auth
TOKEN_URL= # i.e. https://oauth2.googleapis.com/token
USER_INFO_URL=  # Optional: Override provider's default user info endpoint
LOGOUT_URL=  # Optional: Provider logout URL for SSO logout

# Security Configuration
JWT_SECRET=generate-secure-random-string-minimum-32-characters
ALLOW_ALL_USERS=false # Set to true to allow any authenticated user

# Service Configuration
LOG_LEVEL=info  # Options: debug, info, warn, error
TERMINATE_TLS=true  # Set to false if terminating TLS upstream
```

Replace all placeholder values with your actual configuration details. Generate
cryptographically secure random strings for the JWT secret using a tool like
`openssl rand -hex 32`.

For OAuth provider configuration, adjust the AUTH_URL and TOKEN_URL based on your chosen provider. Common configurations include:

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

Depending on your security posture, you might choose to setup stricter authentication between the services and the database.
To do so, set the values of:

```bash
POSTGRES_USER=clay # default
POSTGRES_PASSWORD=clay-password # default
```

## TLS Certificate Configuration

The Doubleword Control Layer must be served with TLS secure operation. You can
configure TLS termination in two ways depending on your infrastructure
requirements and security policies.

### TLS Termination in the included Nginx server (Recommended)

The default configuration terminates TLS at the nginx service, which handles
SSL/TLS encryption for all incoming connections. This approach simplifies
certificate management.

Create a directory for your certificates (relative to the location of
`docker-compose.yml`) and place your SSL certificate files there:

```bash
mkdir -p authn/nginx/certs
cp /path/to/your/fullchain.pem authn/nginx/certs/tls.crt
cp /path/to/your/privkey.pem authn/nginx/certs/tls.key
```

For production use with Let's Encrypt, you can use certbot to generate and
automatically renew certificates:

```bash
certbot certonly --standalone -d your-production-domain.com
ln -s /etc/letsencrypt/live/your-production-domain.com/fullchain.pem authn/nginx/certs/tls.crt
ln -s /etc/letsencrypt/live/your-production-domain.com/privkey.pem authn/nginx/certs/tls.key
```

Ensure the TERMINATE_TLS environment variable is set to `true` (the default) in
your .env file.

### TLS Termination Downstream

If you're planning to terminate the TLS connection upstream (e.g., at a load
balancer or reverse proxy), set the `TERMINATE_TLS` environment variable to
`false`

## Starting the Services

Launch the Control Layer services using Docker Compose. The system will
automatically download required container images, initialize the database, and
start all services in the correct order.

```bash
docker compose up -d --wait
```

The initial startup process may a minute while Docker downloads images and the
database performs initial setup. The command will detach once the containers
are running, allowing you to continue using the terminal.

To check the logs after you've detached, you can use:

```bash
docker compose logs -f
```
