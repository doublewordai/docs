# Model Sources

Model sources connect the Control Layer to AI inference endpoints. As an
administrator, you configure these connections to make models available to your
users.

## Understanding Model Sources

A model source represents a connection to an AI provider like OpenAI,
Anthropic, or any OpenAI-compatible endpoint. Each source can provide multiple
models, which the Control Layer discovers automatically through synchronization.

Model sources require specifying:

- The API endpoint URL
- Depending on the provider: authentication credentials (typically an API key)

Once configured, Control Layer maintains the connection and keeps the model
list current through periodic synchronization.

## Adding Model Sources

Model sources can be configured in two ways:

1. In the initial setup of the application. See
   [configuration](../../reference/configuration) for details.
2. Dynamically, via the web interface.
Configure initial model sources in `clay_config.yaml` before first startup:

After initial setup, manage model sources through the web interface. The
configuration file is only read during initial database creation – subsequent
changes must be made through the application.

## Supported Providers

Control Layer supports any OpenAI-compatible API. Common providers include:

**Self-hosted models**: Connect to self-hosted models running the Doubleword
inference stack, or any source that provides an openAI compatible API.
Depending on how the stack is deployed, the control layer can be used as the
authentication layer for an unauthenticated openAI-compatible API.

**OpenAI**: The standard OpenAI API endpoint provides access to GPT models. Use
your OpenAI API key for authentication.

**Alternative Providers**: Services like Together, Replicate, or Hugging Face
that offer OpenAI-compatible endpoints work seamlessly.

## Model Discovery and Synchronization

Control Layer automatically discovers available models from each source. The
synchronization process:

1. Queries the provider's model list endpoint
2. Updates the database with new models
3. Marks unavailable models as offline
4. Logs any errors or issues

Synchronization runs automatically based on a configurable interval (default 30s).

## Managing Provider API Keys

Provider API keys authenticate the Control Layer with model providers. These
keys are sensitive – they control access to paid services.  

They're stored securely in the control layer database. If these credentials are
exposed elsewhere, they can be used to access your models and incur costs. If
this happens, make sure you rotate the keys immediately.

## Troubleshooting

**Models not appearing**: Check synchronization logs for errors. Verify the API
key is valid and has appropriate permissions. Ensure the endpoint URL is
correct.

**Authentication failures**: API keys might be expired, revoked, or lack
necessary permissions. Test keys directly with the provider's API to isolate
issues.

**Synchronization failures**: Network issues, provider outages, or API changes
can cause sync failures. Check provider status pages and Control Layer logs.

## Best Practices

**Organize sources logically**: Use descriptive names that indicate the
provider or purpose, like "openai-production" or "anthropic-development".

**Document your sources**: Maintain documentation about which API keys are
used, their purpose, and who manages them.

**Plan for failures**: Have backup sources or alternative models available if
primary sources fail.

**Separate environments**: Use different API keys and possibly different
sources for development, staging, and production.
