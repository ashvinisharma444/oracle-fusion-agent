"""
Gemini 2.5 Pro adapter implementing the AIProvider interface.
Handles structured output, retry logic, token management, and image analysis.
"""
import asyncio
import base64
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from app.config.settings import get_settings
from app.core.exceptions import AIProviderError, AIRateLimitError, AIResponseParseError
from app.core.logging import get_logger
from app.domain.interfaces.ai_port import AIProvider, DiagnosticResult, RCAReport, Severity
from app.infrastructure.ai.prompts.rca_analysis import (
    RCA_OUTPUT_SCHEMA,
    build_screenshot_analysis_prompt,
    build_subscription_rca_prompt,
    build_order_rca_prompt,
    build_orchestration_rca_prompt,
)

logger = get_logger(__name__)
settings = get_settings()

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

MODULE_PROMPT_BUILDERS = {
    "subscription": build_subscription_rca_prompt,
    "order": build_order_rca_prompt,
    "orchestration": build_orchestration_rca_prompt,
}


class GeminiAdapter(AIProvider):
    """Google Gemini 2.5 Pro implementation of AIProvider."""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        generation_config = genai.GenerationConfig(
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            response_mime_type="application/json",
        )
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=generation_config,
            safety_settings=SAFETY_SETTINGS,
        )
        self._vision_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                response_mime_type="application/json",
            ),
            safety_settings=SAFETY_SETTINGS,
        )
        logger.info("gemini_adapter_initialized", model=settings.GEMINI_MODEL)

    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        context: str,
        module: str,
        additional_context: Optional[str] = None,
    ) -> DiagnosticResult:
        prompt = build_screenshot_analysis_prompt(module, context)
        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"

        image_part = {"mime_type": "image/png", "data": base64.b64encode(image_bytes).decode()}

        raw_response = await self._call_with_retry(
            self._vision_model, [prompt, image_part]
        )
        return self._parse_to_diagnostic_result(raw_response, module)

    async def generate_rca(
        self,
        page_data: Dict[str, Any],
        knowledge_context: List[str],
        module: str,
        transaction_ref: str,
    ) -> RCAReport:
        prompt_builder = MODULE_PROMPT_BUILDERS.get(module.lower(), build_subscription_rca_prompt)
        prompt = prompt_builder(page_data, knowledge_context)

        raw_response = await self._call_with_retry(self._model, [prompt])
        diagnostic = self._parse_to_diagnostic_result(raw_response, module)

        return RCAReport(
            diagnostic_result=diagnostic,
            transaction_reference=transaction_ref,
            module=module,
            page_data_summary=str(page_data)[:500],
            knowledge_context_used=knowledge_context[:5],
            screenshots_analyzed=[],
            generated_at=datetime.utcnow(),
        )

    async def structured_query(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        full_prompt = f"{prompt}\n\nRespond with JSON matching schema: {json.dumps(response_schema)}"
        if context:
            full_prompt = f"Context:\n{context}\n\n{full_prompt}"
        raw = await self._call_with_retry(self._model, [full_prompt])
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise AIResponseParseError(f"Failed to parse structured response: {e}", {"raw": raw[:500]})

    async def health_check(self) -> bool:
        try:
            response = await asyncio.to_thread(
                self._model.generate_content,
                ["Respond with: {\"status\": \"ok\"}"],
            )
            return "ok" in (response.text or "").lower()
        except Exception as e:
            logger.error("gemini_health_check_failed", error=str(e))
            return False

    async def _call_with_retry(self, model: genai.GenerativeModel, parts: list) -> str:
        last_error = None
        for attempt in range(1, settings.GEMINI_MAX_RETRIES + 1):
            try:
                start = time.perf_counter()
                response = await asyncio.to_thread(model.generate_content, parts)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)

                text = response.text or ""
                tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0

                logger.info(
                    "gemini_call_success",
                    attempt=attempt,
                    duration_ms=duration_ms,
                    tokens=tokens,
                )
                return text

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning("gemini_call_failed", attempt=attempt, error=str(e))

                if "quota" in error_str or "rate" in error_str or "429" in error_str:
                    wait_time = settings.GEMINI_RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.info("gemini_rate_limit_backoff", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)
                elif "503" in error_str or "unavailable" in error_str:
                    await asyncio.sleep(settings.GEMINI_RETRY_DELAY_SECONDS * attempt)
                else:
                    raise AIProviderError(f"Gemini API error: {e}")

        if "quota" in str(last_error).lower() or "rate" in str(last_error).lower():
            raise AIRateLimitError(f"Gemini rate limit exceeded after {settings.GEMINI_MAX_RETRIES} retries")
        raise AIProviderError(f"Gemini failed after {settings.GEMINI_MAX_RETRIES} retries: {last_error}")

    def _parse_to_diagnostic_result(self, raw_response: str, module: str) -> DiagnosticResult:
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except Exception:
                    data = {}
            else:
                data = {}

        severity_str = data.get("severity", "medium").lower()
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.MEDIUM

        return DiagnosticResult(
            root_cause=data.get("root_cause", "Unable to determine root cause from available data"),
            root_cause_detail=data.get("root_cause_detail", ""),
            severity=severity,
            confidence_score=float(data.get("confidence_score", 0.5)),
            impacted_modules=data.get("impacted_modules", [module]),
            recommended_diagnostics=data.get("recommended_diagnostics", []),
            suggested_next_steps=data.get("suggested_next_steps", []),
            supporting_evidence=data.get("supporting_evidence", []),
            raw_ai_response=raw_response[:2000],
            model_used=settings.GEMINI_MODEL,
            tokens_used=0,
            metadata={"oracle_doc_references": data.get("oracle_doc_references", [])},
        )


_gemini_adapter: Optional[GeminiAdapter] = None


def get_ai_provider() -> AIProvider:
    global _gemini_adapter
    if _gemini_adapter is None:
        _gemini_adapter = GeminiAdapter()
    return _gemini_adapter
