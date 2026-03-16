# Huggingface Integration Guidance

Overview

1. Purpose: Guidance for adding Huggingface model support to this codebase.

Suggested integration approach

1. Add a new service module at `app/services/hf_service.py` that exposes async functions similar to those in `app/services/llm_service.py`.
2. The new module should provide the same public interface used by the rest of the application, for example `generate_docstring` and `explain_code`.

Example configuration and dependencies

1. Add `transformers` and `accelerate` to `requirements.txt` when using local or hosted Huggingface runtimes.
2. Example `.env` entries:
   1. `LLM_PROVIDER=huggingface`
   2. `HF_MODEL_NAME=meta-llama/Llama-2-7b` or another model id depending on hosting strategy.

Operational options

1. Hosted inference: Use Huggingface Inference API with an API token stored in an environment variable. Ensure network security and rate limit handling.
2. Local inference: Host a model with `transformers` and accelerate on appropriate hardware.

Implementation notes

1. Maintain a consistent async interface so the API layer does not need branching logic to support different providers.
2. Implement robust error handling and fallbacks to avoid breaking higher level workflows.

Testing

1. Mock `app/services/hf_service.py` in unit tests.
2. Provide small functional tests that validate tokenization and model response parsing.

Security and privacy

1. Avoid sending sensitive code or data to third party inference endpoints unless authorized.
2. Log minimal model metadata and use secure storage for tokens.
