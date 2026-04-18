GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
GEMINI_3_FLASH_PREVIEW_INPUT_TOKENS = 1_048_576
GEMINI_3_FLASH_PREVIEW_OUTPUT_TOKENS = 65_536
GEMINI_3_FLASH_PREVIEW_THINKING_LEVEL = "high"


def normalize_model_name(model: str) -> str:
    if not model:
        return ""

    normalized = model
    prefixes = ("[EXPRESS] ", "[PAY]")
    suffixes = (
        "-openai",
        "-auto",
        "-search",
        "-encrypt-full",
        "-encrypt",
        "-nothinking",
        "-max",
    )

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                changed = True
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                changed = True

    return normalized


def is_gemini_3_flash_preview(model: str) -> bool:
    return normalize_model_name(model) == GEMINI_3_FLASH_PREVIEW


def apply_gemini_3_flash_rest_generation_config(model: str, generation_config: dict) -> dict:
    if not is_gemini_3_flash_preview(model):
        return generation_config

    generation_config["maxOutputTokens"] = GEMINI_3_FLASH_PREVIEW_OUTPUT_TOKENS
    thinking_config = generation_config.setdefault("thinkingConfig", {})
    thinking_config.pop("thinkingBudget", None)
    thinking_config["thinkingLevel"] = GEMINI_3_FLASH_PREVIEW_THINKING_LEVEL
    return generation_config


def apply_gemini_3_flash_sdk_generation_config(model: str, generation_config: dict) -> dict:
    if not is_gemini_3_flash_preview(model):
        return generation_config

    generation_config["max_output_tokens"] = GEMINI_3_FLASH_PREVIEW_OUTPUT_TOKENS
    thinking_config = generation_config.setdefault("thinking_config", {})
    thinking_config.pop("thinking_budget", None)
    thinking_config["thinking_level"] = GEMINI_3_FLASH_PREVIEW_THINKING_LEVEL
    return generation_config


def apply_gemini_3_flash_openai_params(model: str, params: dict) -> dict:
    if not is_gemini_3_flash_preview(model):
        return params

    params["max_tokens"] = GEMINI_3_FLASH_PREVIEW_OUTPUT_TOKENS
    params["reasoning_effort"] = GEMINI_3_FLASH_PREVIEW_THINKING_LEVEL
    return params
