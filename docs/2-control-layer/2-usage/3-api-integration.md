# Interacting via the API

The Control Layer provides an OpenAI-compatible API for programmatic access to AI
models. This allows you to integrate AI capabilities into your applications
using familiar tools and libraries.

Clicking on the API button for any model in the 'models' view will open a menu in which you can view interactive snippets for various programming languages, including Python and Node.js.

![OpenAI-compatible API example](/img/control-layer-api-example.png)
*Using the Control Layer with the OpenAI Python SDK - simply change the base_url and api_key*

## API Keys

Generate API keys through the API Keys page to authenticate your applications.
Each key is tied to your user account and inherits your group permissions –
your applications can only access models available to you.

Create separate keys for different applications or environments. This practice
improves security and makes it easier to track usage or revoke access if
needed. You can maintain multiple active keys, allowing smooth key rotation
without downtime.

Store API keys securely. Never commit them to version control or expose them in
client-side code. Treat them like passwords. If a key is compromised, revoke it
immediately and generate a new one.

## OpenAI Compatibility

The Control Layer API implements the OpenAI API specification. This means you
can use existing OpenAI client libraries and tools by simply changing the
endpoint URL and API key. No code changes are required beyond configuration.

This compatibility extends to:

**Official SDKs**: Use OpenAI's Python, Node.js, and other official libraries
by configuring the base URL.

**Third-party tools**: Any tool that supports OpenAI's API can work with
the Control Layer through configuration.

**Existing applications**: Migrate OpenAI-based applications by updating just
the endpoint and authentication details.

## Configuration

Point your OpenAI client to the Control Layer endpoint instead of OpenAI's
servers. The base URL follows this pattern:

``` https://your-control-layer-instance/ai/v1 ```

For example, in Python:

```python
from openai import OpenAI

client = OpenAI( 
    base_url="https://your-control-layer-instance/ai/v1",
    api_key="your-control-layer-api-key"
) 
```

In Node.js:

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({ 
      baseURL: 'https://your-control-layer-instance/ai/v1', 
      apiKey: 'your-control-layer-api-key', 
}); 
```

These snippets are available on the [models
page](https://your-control-layer-instance/models) for each model, making it
easy to copy and paste the correct configuration.

## Making Requests

Use model identifiers exactly as they appear in your available models list.
Control Layer automatically routes your request to the appropriate provider.

```python
response = client.chat.completions.create( 
  model="gpt-4",  # Or any model you have access to 
  messages=[{"role": "user", "content": "Hello!"}]
)
```

The API handles authentication with underlying providers transparently. You
only need your Control Layer API key, regardless of whether the model comes
from OpenAI, Anthropic, or another provider.

## Request Routing

Control Layer intelligently routes each request based on the model identifier.
You don't need to know which provider hosts a model or manage multiple
endpoints and API keys.

If a model becomes unavailable, the API returns an appropriate error. Your
application should handle these errors gracefully, potentially retrying with a
different model or alerting users to the issue.

## Streaming Responses

The API supports streaming responses for compatible models, allowing you to
receive partial results as they're generated:

```python
stream = client.chat.completions.create( model="gpt-4",
messages=[{"role": "user", "content": "Tell me a story"}], stream=True)

for chunk in stream: if chunk.choices[0].delta.content:
  print(chunk.choices[0].delta.content, end="") 
```

Streaming reduces perceived latency in interactive applications by showing
partial results immediately.

## Error Handling

Implement robust error handling to manage various failure scenarios:

**Authentication errors**: Verify your API key is valid and not revoked.

**Model unavailable**: The requested model might be temporarily offline.
Consider implementing fallback models.

**Rate limits**: Respect rate limits and implement exponential backoff for
retries.

**Token limits**: Handle cases where requests exceed the model's context window
by truncating or splitting content.

**Network issues**: Implement timeouts and retries for transient network
failures.

## Best Practices

**Use appropriate models**: Match model capabilities to your task. Don't use
expensive, powerful models for simple tasks.

**Implement caching**: Cache responses for identical requests to reduce costs
and latency.

**Monitor usage**: Track API calls to understand consumption patterns and
detect anomalies.

**Handle failures gracefully**: Always have a plan for when models are
unavailable or requests fail.

**Secure your keys**: Rotate keys periodically and never expose them in
client-side code or logs.

## Migrating from Direct Provider Access

If you're migrating from direct OpenAI or Anthropic API access, the transition
is straightforward:

1. Generate a Control Layer API key
2. Update your base URL to point to Control Layer
3. Replace your provider API key with your Control Layer key
4. Ensure model names match those available in Control Layer

Your application code remains unchanged. The Control Layer handles
provider-specific details transparently.
