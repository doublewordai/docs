# Viewing available models

The Models page provides an overview of all AI models available to you through
the Doubleword Control Layer.

The Models page displays all models you have access to through your
group memberships. Each model card shows comprehensive information to help you
choose the right model for your task.

The page organizes models by their source provider (OpenAI, Anthropic, or
custom endpoints), making it easy to understand which service powers each
model. This organization helps when you need specific provider features, or want
to compare models from the same family.

Each model has an API examples tab, showing how to use the model API, and a
Playground tab, providing an interactive interface to test the model directly
in your browser.

![Models Page](/img/models.png)

### For administrators

Clicking through on a model card will give you additional information about that model. As an administrator, you can use these pages to configure the models behaviour - for example, setting the model type will change what playground will be displayed for the model.

Clicking the 'Add groups' button lets you change which user groups have access
to the model. Navigate to the Users & Groups tab to manage group memberships. User-group-model assignments are evaluated at request time, so changes take effect immediately.

## How to refer to a model

Each model card on the page includes both the **alias** for the model - at the
top, in bold - and the specific **model name** (below). These might be the
same. The alias is the name that's used to refer to the model in API calls, or
in the playground.

Administrators can choose to change either the alias or the underlying
model - this can be useful, for example, for making your LLM API stable, even
if the underlying model changes.

## Staying Informed

For users, the models page updates automatically as:

- New models become available from providers
- Model availability status changes
- Your group memberships change
- Administrators add or remove model sources

Check the page regularly if you're waiting for access to new models or
experiencing issues with model availability.

## Next Steps

Once you've identified the models available to you:

- Use the [Playground](playground) to test models interactively
- Generate [API keys](api-integration) for programmatic access
- Review model-specific documentation from providers for advanced features
