# Adding new endpoints

Once we've got the Control Layer running (see [Getting Started](../../getting-started/) for how), we need to add models to interact with.

Model sources in the Control Layer are referred to as "Endpoints". An endpoint
is an accessible URL that exposes AI models via an OpenAI-compatible API.

:::tip What do we mean by an OpenAI-Compatible API?
OpenAI is a popular provider of LLM APIs. Their REST API has become a de-facto standard for interacting with large language models over the internet.
Most other providers expose an OpenAI-compatible API.
:::

You configure these connections to make models available to users of your Control Layer.

## Understanding Model Sources

An endpoint represents a connection to an AI provider like OpenAI,
Anthropic, or any OpenAI-compatible endpoint. Each source can provide multiple
models, which the Control Layer discovers automatically through synchronization.

Model sources require specifying:

- The API endpoint URL
- Depending on the provider: authentication credentials (typically an API key)

## Adding Model Sources

Model sources can be configured in two ways:

1. In the initial setup of the application. See
   [configuration](../../reference/configuration) for details.
2. Dynamically, via the web interface.

After initial setup, manage model sources through the web interface. The
configuration file is only read during initial database creation – subsequent
changes must be made through the application.

## Supported Providers

Control Layer supports any OpenAI-compatible API (and more, see [Endpoint technical requirements](#endpoint-technical-requirements) for details). Commonly used providers include:

**OpenAI**: The standard OpenAI API endpoint provides access to GPT models. Use
your OpenAI API [key](https://platform.openai.com/api-keys) for authentication.

**Claude**: connect to Anthropic's Claude models using their OpenAI-compatible API. Generate keys in the anthropic [console](https://console.anthropic.com/settings/keys).

**Gemini**: connect to Google's Gemini models using their OpenAI-compatible API. Generate keys in the AI [studio](https://aistudio.google.com/api-keys).

**Self-hosted models**: Connect to self-hosted models running the Doubleword
inference stack, or any source that provides an openAI compatible API (vLLM,
SGLang, etc.). Depending on how the stack is deployed, the control layer can be
used as the authentication layer for an unauthenticated openAI-compatible API.

**Alternative Providers**: Services like Together, Replicate, or Hugging Face
that offer OpenAI-compatible endpoints work seamlessly.

## Model Discovery and Synchronization

Control Layer automatically discovers available models from each source. The
synchronization process:

1. Queries the provider's model list endpoint
2. Updates the database with new models
3. Marks unavailable models as offline
4. Logs any errors or issues

If the details of the endpoint have changed (you've updated the API key, or the
provider has released a new model), navigate to the endpoints page, an click
the synchronize button for the relevant endpoint.

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

##  Endpoint technical requirements

The Doubleword control layer works by proxying requests to inference endpoints.
It doesn't have to understand the full details of the API exposed by the
endpoint in order to do so. All OpenAI compatible endpoints are supported, but
the API format is not actually that restrictive.

In order to add an inference endpoint, to the Doubleword Control Layer, it must
do two things:

1. Support the openAI `GET /v1/models` [route](https://platform.openai.com/docs/api-reference/models). The Control Layer uses this to discover and display the available models at that endpoint.
2. Specify its "model" parameter in the JSON body of requests. For example, OpenAI's "/chat/completions" route accepts requests that look like `{"model":"gpt-4", ...}`.

This is broader than openAI compatibility - there's no reference here to the
specific form of the request that needs to be made. For example, you can send
requests through the control layer to Claude
[models](https://docs.claude.com/en/api/messages) using Anthropic's messages
API.
