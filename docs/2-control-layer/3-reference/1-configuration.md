---
sidebar_label: Configuration
---
# Configuration Reference

The control Layer uses a YAML configuration file to manage its core settings. The
system reads from `clay_config.yaml` by default and supports environment
variable overrides for all settings.

## Configuration File Location

The configuration file should be named `clay_config.yaml` and placed in the
application root directory. The system will read this file on startup to
configure the Clay API server and its connections.

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

### Database Connection

Control Layer requires a PostgreSQL database for persistent storage of users,
groups, models, and configuration data.

```yaml
database_url: "postgres://username@hostname:5432/database_name"
```

The database URL follows the standard PostgreSQL connection string format. It
includes the username, hostname, port, and database name. The system expects
the database to exist and will run migrations automatically on startup.

### Admin User

The system requires an initial admin user for bootstrapping access control.
This user is created automatically on first startup if it doesn't already
exist.

```yaml
admin_email: "admin@example.com"
```

This email address becomes the primary administrator account. Additional admin
users must be created through the web interface after signing in with this
initial account. The admin email must be a valid email address that matches
your authentication provider's user directory.

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

## Environment Variable Overrides

Any top-level configuration setting can be overridden using environment
variables. Environment variables take precedence over values in the
configuration file.

Most settings use the `CLAY_` prefix followed by the uppercased setting name:

```bash
CLAY_HOST=127.0.0.1
CLAY_PORT=8080
CLAY_ADMIN_EMAIL=newadmin@example.com
```

The database URL is a special case and uses the standard `DATABASE_URL`
environment variable without the `CLAY_` prefix:

```bash
DATABASE_URL=postgres://prod@db:5432/production_db
```

Environment variable overrides are particularly useful for:

- Storing sensitive values like API keys outside of configuration files

## Configuration Validation

The system validates configuration on startup and will fail to start if
required settings are missing or invalid. Required settings include:

- A valid database URL that can be connected to
- An admin email address in valid email format
- A host and port that can be bound to

Model sources are validated when they're used, not at startup. Invalid model
sources will log errors but won't prevent the system from starting.
