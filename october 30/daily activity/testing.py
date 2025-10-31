import litellm

print("Sending request to OpenRouter...\n")

resp = litellm.completion(
    model="mistralai/mistral-7b-instruct",
    messages=[{"role": "user", "content": "Give me three fun facts about AI"}],
    api_base="https://openrouter.ai/api/v1",
    api_key="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",
    custom_llm_provider="openai"
)

print("\n--- Model Output ---")
print(resp["choices"][0]["message"]["content"])
