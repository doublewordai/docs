# Monitoring model status

Control Layer provides built-in health monitoring for your AI model endpoints.
For models for which monitoring is configured, The status indicator shows at a
glance whether models are online and responding correctly.

## Understanding Model Status

Each model in the overview page displays a status indicator showing its current health:

- **Green dot**: Model is online and responding to health checks
- **Red dot**: Model is offline or failing health checks

## Setting Up Monitoring

Administrators can configure monitoring from the model information page.
Control Layer supports two types of health checks:

### Default Monitors

Control Layer automatically configures appropriate health checks based on the
model type:

- **Chat models**: Uses a `/v1/chat/completions` endpoint ping
- **Embedding models**: Uses a `/v1/embeddings` endpoint ping

These default monitors provide zero-configuration health checking for standard
model types.

:::tip Active vs passive monitoring
The control layer uses 'active' monitoring, meaning it periodically sends real
requests to the endpoints to verify they are functioning correctly. Currently,
user requests do not influence model status.

These active requests are configured to be as lightweight as possible. Frequent
pings to expensive models will incur costs - so make sure to configure the
check interval appropriately, or switch to a custom probe.
:::

### Custom HTTP Probes

You can also configure a custom HTTP probe with:

- **Path**: The endpoint path to check (e.g., `/health`, `/status`)
- **Method**: HTTP method to use (GET, POST, etc.)
- **Body**: Optional request body for POST/PUT requests

Custom probes are useful for higher level monitoring (i.e. is the endpoint
online), non-standard endpoints, or when you need to verify specific functionality.

## Managing Monitors

Once a monitor is active, admins can manage it from the model information page:

- **Pause**: Temporarily stop health checks without removing the configuration
- **Edit**: Modify the probe configuration, check interval, or other settings
- **Stop**: Remove the monitor entirely

Changes to monitoring configuration take effect immediately.

## Viewing Historical Uptime

The [models overview page](../models-and-access) includes a tab toggle in the
top right corner that displays historical uptime data for all visible models with configured monitoring.
This view shows:

- Model availability trends over time
- Incident history and outage duration
- Comparative uptime across different model sources

You can use this as a status page to display model reliability to your users,
and allow them to plan accordingly.

## Troubleshooting

**False negatives (red dot but model works)**: Check that the monitoring probe
matches the model's actual API. Some endpoints may not support standard OpenAI
routes.

**Intermittent status changes**: May indicate rate limiting, network issues, or
provider instability. Check the detailed probe information for error messages.

**Missing uptime data**: Historical data begins accumulating when monitoring
starts. Newly monitored models won't have historical trends initially.
