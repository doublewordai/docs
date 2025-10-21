---
sidebar_label: Configuration
---
# Configuration Reference

The Control Layer uses a YAML configuration file to manage its core settings. The
system reads from `config.yaml` by default and supports environment
variable overrides for all settings.

## Configuration File Location

The configuration file should be named `config.yaml` and can be:
- Placed in the application root directory
- Mounted into a Docker container at `/app/config.yaml`
- Placed alongside `docker-compose.yml` (automatically mounted)

The system will read this file on startup to configure the Control Layer server and its connections.

## Environment Variable Overrides

Any configuration setting can be overridden using environment variables prefixed with
`DWCTL_`. Your custom values will be merged with the default configuration.

Nested sections can be specified by joining keys with a double underscore. For example:
- To disable native authentication: `DWCTL_AUTH__NATIVE__ENABLED=false`
- To change the port: `DWCTL_PORT=8080`
- To set the database URL: `DATABASE_URL=postgres://...` (special case, no prefix)

## Core Settings

### Server Configuration

The server configuration controls how the Clay API service binds to network
interfaces and which port it uses.

```yaml
host: "0.0.0.0"
port: 3001
```

The `host` parameter determines which network interface the server binds to.
Setting it to `0.0.0.0` makes the server accessible from any network interface.
For security reasons, you might want to restrict this to `127.0.0.1` for
local-only access or a specific IP address in production environments.

The `port` parameter specifies which TCP port the server listens on. The
default is 3001, but this can be changed to avoid conflicts with other
services.

### Database Configuration

The Control Layer requires a PostgreSQL database for persistent storage of users,
groups, models, and configuration data.

```yaml
database:
  type: external  # or 'embedded' (requires special build)
  url: "postgres://localhost:5432/control_layer"
```

The database URL follows the standard PostgreSQL connection string format. It
includes the username, hostname, port, and database name. The system expects
the database to exist and will run migrations automatically on startup.

You can also set the database URL via the `DATABASE_URL` environment variable (recommended for production):
```bash
DATABASE_URL=postgres://username@hostname:5432/database_name
```

#### Embedded Database (Advanced)

Alternatively, you can use embedded postgres (requires compiling with the
`embedded-db` feature, which is not present in the default docker image):

```yaml
database:
  type: embedded
  data_dir: "/path/to/data"  # Optional: directory for database storage
  persistent: false  # Set to true to persist data between restarts
```

### Admin User

The system requires an initial admin user for bootstrapping access control.
This user is created automatically on first startup if it doesn't already
exist.

```yaml
admin_email: "test@doubleword.ai"
admin_password: "hunter2"
```

:::danger
Change the default admin password immediately in production!
:::

This email address becomes the primary administrator account. Additional admin
users must be created through the web interface after signing in with this
initial account.

### Secret Key

A secret key is required for JWT signing when native authentication is enabled.

```yaml
secret_key: "your-secret-key-here"
```

This can also be set via the `SECRET_KEY` environment variable. Generate a secure random key using:
```bash
openssl rand -base64 32
```

## Authentication Configuration

The Control Layer supports multiple authentication methods that can be configured independently.

### Native Authentication

Native username/password authentication stores users in the local database and allows them to login at `http://<host>:<port>/login`.

```yaml
auth:
  native:
    enabled: true  # Enable native login system
    allow_registration: false  # Whether users can sign up themselves
    password:
      min_length: 8
      max_length: 64
    session:
      timeout: "24h"
      cookie_name: "dwctl_session"
      cookie_secure: true
      cookie_same_site: "strict"
```

When `allow_registration` is `false` (recommended for security), admins must create new users via the interface or API.

### Proxy Header Authentication

Accepts and auto-creates users based on email addresses supplied in a configurable header. This lets you use an upstream proxy (like an identity-aware proxy) to authenticate users.

```yaml
auth:
  proxy_header:
    enabled: false
    header_name: "x-doubleword-user"
    groups_field_name: "x-doubleword-user-groups"
    blacklisted_sso_groups:
      - "t1"
      - "t2"
    provider_field_name: "x-doubleword-sso-provider"
    import_idp_groups: false
    auto_create_users: true
```

When `auto_create_users` is `false`, users must be pre-created by an admin. Users that aren't pre-created will receive a 403 Forbidden error.

### Security Settings

Controls session expiry and CORS settings.

```yaml
auth:
  security:
    jwt_expiry: "24h"  # How long session cookies are valid
    cors:
      allowed_origins:
        - "http://localhost:3001"
      allow_credentials: true
      max_age: 3600  # Cache preflight requests for 1 hour
```

:::warning
In production, make sure your frontend URL is listed in `allowed_origins`.
:::

## Model Sources

Model sources define the AI inference endpoints that the Control Layer can
connect to. These are configured as a list of sources, each with its own
connection parameters.

```yaml
model_sources: []
```

Each model source requires several parameters:

```yaml
model_sources:
  - name: "openai"
    url: "https://api.openai.com"
    api_key: "sk-..."
    sync_interval: "30s"
```

The `name` field provides a unique identifier for the model source. This name
is used internally to track models and their origins.

The `url` field specifies the base URL of the inference endpoint. This should
be the root URL without any path components.

The `api_key` field contains the authentication token for the model source.
This is required for commercial APIs like OpenAI and Anthropic. For internal
services, this field may be omitted if no authentication is required.

The `sync_interval` field determines how often the system queries the model
source for available models. This accepts duration strings like "30s", "1m", or
"5m". Shorter intervals provide more up-to-date model lists but increase API
usage.

### Supported Model Sources

The Control Layer supports any OpenAI-compatible model provider.
For the purposes of setting up model sources in configuration, this means:

1. The provider must have a `v1/models` endpoint that returns a list of
   available models.

### Model Source Persistence

Model sources are only seeded from the configuration file on the very first run
when the database is empty. After initial setup, model sources are managed
dynamically through the API. Changes to the `model_sources` configuration
after initial setup will not be reflected in a running system with a 'seeded'
database.

## Frontend Metadata

The metadata section configures display information shown in the web interface header.

```yaml
metadata:
  region: "UK South"
  organization: "ACME Corp"
```

The `region` field displays the deployment region or data center location. This
helps users understand where their requests are being processed.

The `organization` field shows the name of the organization running this
Control Layer instance. This provides context in multi-tenant or multi-region
deployments.

## Request Logging

By default, the Control Layer logs all requests and responses to the database asynchronously, with minimal performance impact.

```yaml
enable_request_logging: true
```

If you have sensitive data in your requests/responses, you can disable logging by setting this to `false`.

## Complete Default Configuration

Here's the complete default configuration with all available options:

```yaml
# Secret key for JWT signing (required in production when native auth is enabled)
# secret_key: null  # Must be provided via env var or config

# Admin user - created on first startup
admin_email: "test@doubleword.ai"
admin_password: "hunter2"  # TODO: Change in production!

# Authentication configuration
auth:
  native:
    enabled: true
    allow_registration: false
    password:
      min_length: 8
      max_length: 64
    session:
      timeout: "24h"
      cookie_name: "dwctl_session"
      cookie_secure: true
      cookie_same_site: "strict"

  proxy_header:
    enabled: false
    header_name: "x-doubleword-user"
    groups_field_name: "x-doubleword-user-groups"
    blacklisted_sso_groups:
      - "t1"
      - "t2"
    provider_field_name: "x-doubleword-sso-provider"
    import_idp_groups: false
    auto_create_users: true

  security:
    jwt_expiry: "24h"
    cors:
      allowed_origins:
        - "http://localhost:3001"
      allow_credentials: true
      max_age: 3600

# Model sources seeded on first boot
model_sources: []
# Example:
# model_sources:
#   - name: "openai"
#     url: "https://api.openai.com"
#     api_key: "sk-..."

# Frontend metadata
metadata:
  region: "UK South"
  organization: "ACME Corp"

# Server configuration
host: "0.0.0.0"
port: 3001

# Database configuration
database:
  type: external
  url: "postgres://localhost:5432/control_layer"

# Request logging
enable_request_logging: true
```

## Configuration Validation

The system validates configuration on startup and will fail to start if
required settings are missing or invalid. Required settings include:

- A valid database URL that can be connected to
- An admin email address in valid email format
- A host and port that can be bound to

Model sources are validated when they're used, not at startup. Invalid model
sources will log errors but won't prevent the system from starting.
