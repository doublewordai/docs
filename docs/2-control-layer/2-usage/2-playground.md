# Playground

The Playground provides an interactive interface for testing and experimenting
with AI models. Use it to explore model capabilities, test prompts, and compare
responses without writing any code.

The playground supports both Generative and Embeddings models. The type of
playground that's shown for a model is determined by the model's type (shown in
the model's details page). The type is automatically determined from the name
using a heuristic - to override it, you can set the `type` field for a model on
the overview page.

This guide will discuss how to use the Playground effectively for generative
models.

## Getting Started

Select any model from your available models to begin a conversation. The
Playground maintains conversation context, allowing natural back-and-forth
interactions just like ChatGPT or Claude's web interface.

Each conversation is independent. Start a new conversation to reset the context
or to try a different approach. You can switch between models mid-conversation
to see how different models respond to the same context.

## Use Cases

The Playground excels at several tasks that would be cumbersome through the
API:

**Prompt Development**: Test and refine prompts interactively before
implementing them in code. Immediate feedback helps you understand what works
and what doesn't.

**Model Comparison**: Send identical prompts to different models to understand
their strengths, weaknesses, and stylistic differences. This helps you choose
the right model for production use.

**Capability Exploration**: Discover what models can do by experimenting with
different types of requests. Try various tasks like analysis, generation,
transformation, and reasoning.

**Quick Tasks**: For one-off tasks that don't justify writing code, the
Playground provides immediate access to AI capabilities.

## Conversation Management

The Playground maintains the full conversation history in the current session.
This context allows models to reference earlier messages, maintain consistency,
and provide relevant follow-up responses.

Long conversations consume more tokens with each request as the entire history
is sent to the model. If responses become slow or you hit token limits, start a
new conversation to reset the context.

Your conversations are not permanently stored. If you need to preserve
important outputs, copy them before leaving the page or starting a new
conversation.

## Model Behavior

Different models exhibit different conversational styles and capabilities. Some
models are more verbose, others more concise. Some excel at technical tasks,
others at creative work. The Playground lets you experience these differences
directly.

Model responses in the Playground match what you'd receive through the API with
equivalent prompts. This consistency means you can prototype in the Playground
and expect similar results in production.

## Limitations

The Playground is designed for testing and experimentation, not production use.
It has several intentional limitations:

**Session-based**: Conversations exist only for your current session and aren't
saved.

**No automation**: The Playground requires manual interaction. For automated or
programmatic use, switch to the API.

## Tips for Effective Use

Write clear, specific prompts. Models respond better to well-defined requests
than vague questions.

Use system prompts or initial instructions to set the model's behavior for the
entire conversation. This is more efficient than repeating instructions in
every message.

When comparing models, use identical prompts for fair comparison. Small wording
changes can significantly affect responses.

If a model isn't responding as expected, try rephrasing your prompt or starting
a new conversation with clearer initial instructions.

## Moving to Production

Once you've developed effective prompts in the Playground, implement them in
your application using the API. The model identifiers shown in the Playground
are exactly what you'll use in API calls.

Remember that while the Playground is great for experimentation, production
applications need proper error handling, retry logic, and potentially fallback
models that the Playground doesn't provide.

