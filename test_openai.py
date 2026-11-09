from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5-nano",
    instructions="Respond briefly and clearly.",
    input="What does MCP stand for in AI integrations? Answer in one sentence.",
    reasoning={"effort": "minimal"},
    max_output_tokens=150,
)

print("\nAI Response:")
print(response.output_text)

print("\nToken Usage:")
print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
