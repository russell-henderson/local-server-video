"""
AI Gateway for centralized LLM API calls.

This module provides a unified interface for interacting with various Large Language Models (LLMs)
for tasks such as metadata enrichment, embedding generation, and general AI assistance.
It includes a provider adapter pattern to allow switching between different LLM providers
(e.g., Gemini, OpenAI, Anthropic) without changing the core application logic.

See docs/GEMINI.md for the consolidated plan.
"""

import os
from typing import List, Dict, Any, Optional

# Placeholder for actual LLM client, to be initialized based on GEMINI_PROVIDER
llm_client = None

class LLMProvider:
    """Abstract base class for LLM providers."""
    def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError

    def generate_metadata(self, transcript: str) -> Dict[str, Any]:
        raise NotImplementedError

class GeminiProvider(LLMProvider):
    """Gemini LLM provider implementation."""
    def get_embedding(self, text: str) -> List[float]:
        # TODO: Implement actual Gemini embedding generation
        print(f"Mocking Gemini embedding for: {text[:50]}...")
        # Return a mock embedding (e.g., a list of zeros for now)
        return [0.0] * 768 # Common embedding dimension

    def generate_metadata(self, transcript: str) -> Dict[str, Any]:
        # TODO: Implement actual Gemini metadata generation
        print(f"Mocking Gemini metadata generation for transcript: {transcript[:100]}...")
        return {
            "title": "Mock Title from Gemini",
            "description": "Mock Description from Gemini based on transcript.",
            "tags": ["mock", "gemini", "llm"]
        }

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    def get_embedding(self, text: str) -> List[float]:
        # TODO: Implement actual OpenAI embedding generation
        print(f"Mocking OpenAI embedding for: {text[:50]}...")
        return [1.0] * 1536 # Common OpenAI embedding dimension

    def generate_metadata(self, transcript: str) -> Dict[str, Any]:
        # TODO: Implement actual OpenAI metadata generation
        print(f"Mocking OpenAI metadata generation for transcript: {transcript[:100]}...")
        return {
            "title": "Mock Title from OpenAI",
            "description": "Mock Description from OpenAI based on transcript.",
            "tags": ["mock", "openai", "llm"]
        }

def initialize_llm_client():
    """Initializes the LLM client based on environment configuration."""
    global llm_client
    provider_name = os.getenv("GEMINI_PROVIDER", "gemini").lower() # Default to gemini

    if provider_name == "gemini":
        llm_client = GeminiProvider()
        print("[AI Gateway] Initialized GeminiProvider (mock)")
    elif provider_name == "openai":
        llm_client = OpenAIProvider()
        print("[AI Gateway] Initialized OpenAIProvider (mock)")
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

def get_embedding(text: str) -> List[float]:
    """Generates an embedding for the given text using the initialized LLM client."""
    if llm_client is None:
        initialize_llm_client()
    return llm_client.get_embedding(text)

def generate_metadata(transcript: str) -> Dict[str, Any]:
    """Generates metadata for a transcript using the initialized LLM client."""
    if llm_client is None:
        initialize_llm_client()
    return llm_client.generate_metadata(transcript)

# Initialize the client on module import
initialize_llm_client()
