# Gemini API Best Practices Reference

A concise reference guide for working with the Google Gemini API in Python applications.

---

## Table of Contents

1. [SDK Migration](#1-sdk-migration)
2. [Client Initialization](#2-client-initialization)
3. [Async Integration](#3-async-integration)
4. [Structured Output](#4-structured-output)
5. [Pydantic Integration](#5-pydantic-integration)
6. [Common Issues](#6-common-issues)

---

## 1. SDK Migration

As of January 2025, the `google-generativeai` package is deprecated. Use `google-genai` instead.

### Old Package (Deprecated)

```bash
pip install google-generativeai
```

```python
import google.generativeai as genai

genai.configure(api_key="...")
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Hello")
```

### New Package (Current)

```bash
pip install google-genai
```

```python
from google import genai

client = genai.Client(api_key="...")
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Hello"
)
```

---

## 2. Client Initialization

### Basic Setup

```python
from google import genai

# Initialize client with API key
client = genai.Client(api_key="your-api-key")
```

### With Environment Variables

```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
```

### Model Selection

Available models (as of January 2025):
- `gemini-2.5-flash-lite` - Fast, cost-effective for most tasks
- `gemini-2.5-pro` - More capable for complex reasoning
- `gemini-2.0-flash` - Balanced performance

---

## 3. Async Integration

The Gemini SDK's `generate_content` method is synchronous. For async frameworks like FastAPI, wrap it using `asyncio.run_in_executor()`.

### FastAPI Integration

```python
import asyncio
from functools import partial
from google import genai

client = genai.Client(api_key="...")

async def generate_async(prompt: str) -> str:
    """Run Gemini generation in async context."""
    loop = asyncio.get_event_loop()

    func = partial(
        client.models.generate_content,
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    response = await loop.run_in_executor(None, func)
    return response.text
```

### With Structured Output

```python
from pydantic import BaseModel

class MyResponse(BaseModel):
    answer: str
    confidence: float

async def generate_structured_async(prompt: str) -> MyResponse:
    loop = asyncio.get_event_loop()

    func = partial(
        client.models.generate_content,
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": MyResponse.model_json_schema(),
        }
    )

    response = await loop.run_in_executor(None, func)
    return MyResponse.model_validate_json(response.text)
```

---

## 4. Structured Output

**Always use structured output for JSON responses** - it guarantees valid JSON and eliminates parsing errors.

### Basic JSON Schema

```python
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="List 3 programming languages",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": {
            "type": "object",
            "properties": {
                "languages": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["languages"]
        }
    }
)

import json
data = json.loads(response.text)
```

### Key Configuration

- Use `response_json_schema` (NOT `response_schema`)
- Set `response_mime_type` to `"application/json"`

**Documentation**: https://ai.google.dev/gemini-api/docs/structured-output

---

## 5. Pydantic Integration

Use Pydantic models to define schemas and parse responses.

### Define Response Model

```python
from pydantic import BaseModel, Field

class InterviewQuestion(BaseModel):
    question: str = Field(description="The question to ask the user")
    options: list[str] = Field(description="Multiple choice options")

class InterviewResponse(BaseModel):
    questions: list[InterviewQuestion] = Field(description="List of interview questions")
```

### Generate and Parse

```python
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Generate interview questions about Python learning goals",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": InterviewResponse.model_json_schema(),
    }
)

# Parse directly with Pydantic
result = InterviewResponse.model_validate_json(response.text)
```

### Field Descriptions

Add descriptions to Pydantic fields for better model guidance:

```python
class Session(BaseModel):
    title: str = Field(description="Short, descriptive title for the session")
    content: str = Field(description="Detailed markdown content")
    duration_minutes: int = Field(description="Estimated time to complete in minutes")
```

### propertyOrdering Quirk

Gemini requires `propertyOrdering` in the JSON schema for consistent field order. Add it automatically:

```python
def add_property_ordering(schema: dict) -> dict:
    """Add propertyOrdering to schema for Gemini compatibility."""
    if "properties" in schema:
        schema["propertyOrdering"] = list(schema["properties"].keys())

    # Recursively handle nested objects
    for key, value in schema.get("properties", {}).items():
        if isinstance(value, dict):
            add_property_ordering(value)

    # Handle array items
    if "items" in schema and isinstance(schema["items"], dict):
        add_property_ordering(schema["items"])

    return schema

# Usage
schema = add_property_ordering(MyModel.model_json_schema())
```

---

## 6. Common Issues

### JSON Parsing Errors

**Problem**: Response contains markdown code blocks around JSON.

**Solution**: Use structured output (preferred) or clean the response:

```python
import re

def clean_json_response(text: str) -> str:
    """Remove markdown code blocks from JSON response."""
    # Remove ```json ... ``` wrapper
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()
```

### Rate Limiting

**Problem**: Too many requests in short time.

**Solution**: Implement exponential backoff:

```python
import time
from google.genai.errors import ClientError

def generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return response.text
        except ClientError as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
```

### Empty Responses

**Problem**: Model returns empty or minimal response.

**Solution**: Improve prompt clarity and add examples:

```python
prompt = """Generate a learning session about Python basics.

Requirements:
- Title should be 3-7 words
- Content should be 200-300 words in markdown
- Include at least 2 code examples

Example format:
{
    "title": "Variables and Data Types",
    "content": "## Introduction\\n..."
}
"""
```

---

## Resources

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Structured Output Guide](https://ai.google.dev/gemini-api/docs/structured-output)
- [Python SDK Reference](https://ai.google.dev/api/python)
