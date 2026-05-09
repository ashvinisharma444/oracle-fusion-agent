"""
Prompt templates for Oracle Fusion RCA analysis.
All prompts are structured for Gemini 2.5 Pro with JSON schema output.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


SYSTEM_CONTEXT = """
You are an expert Oracle Fusion Cloud Consultant and Principal Technical Architect
with 15+ years of experience in Oracle Fusion Subscription Management, Order Management,
Pricing, Billing, Revenue Management, Installed Base, Orchestration, and Service Contracts.

You specialize in diagnosing complex system behaviors, identifying root causes of failures,
and providing actionable remediation guidance for enterprise Oracle Fusion deployments.

Your analysis is always:
- Technically precise and Oracle-domain-specific
- Based on observable evidence from the UI and page data provided
- Conservative in conclusions (you distinguish confirmed findings from hypotheses)
- Actionable (every finding includes diagnostic steps or remediation)
- Structured for enterprise technical teams

You NEVER fabricate data or make claims not supported by the evidence provided.
"""

RCA_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string", "description": "Concise root cause summary (1-2 sentences)"},
        "root_cause_detail": {"type": "string", "description": "Detailed technical explanation"},
        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "impacted_modules": {"type": "array", "items": {"type": "string"}},
        "recommended_diagnostics": {"type": "array", "items": {"type": "string"}},
        "suggested_next_steps": {"type": "array", "items": {"type": "string"}},
        "supporting_evidence": {"type": "array", "items": {"type": "string"}},
        "oracle_doc_references": {"type": "array", "items": {"type": "string"}},
        "escalation_required": {"type": "boolean"},
    },
    "required": [
        "root_cause", "severity", "confidence_score",
        "impacted_modules", "recommended_diagnostics", "suggested_next_steps",
    ],
}


def build_subscription_rca_prompt(
    subscription_data: Dict[str, Any],
    knowledge_context: List[str],
    issue_description: Optional[str] = None,
) -> str:
    knowledge_block = "\n".join(f"- {k}" for k in knowledge_context) if knowledge_context else "No additional context retrieved."
    issue_block = f"\nReported Issue: {issue_description}" if issue_description else ""
    return f"""{SYSTEM_CONTEXT}

## TASK
Perform a Root Cause Analysis for the Oracle Fusion Subscription Management record below.
Identify any anomalies, configuration issues, data integrity problems, or process failures.{issue_block}

## SUBSCRIPTION DATA EXTRACTED FROM FUSION UI
```json
{_format_json(subscription_data)}
```

## RELEVANT KNOWLEDGE BASE CONTEXT
{knowledge_block}

## ANALYSIS INSTRUCTIONS
1. Review the subscription status, dates, billing account, charges, and any visible error states.
2. Identify any anomalies: invalid status transitions, missing required fields, date conflicts, charge configuration issues.
3. Cross-reference with Oracle Fusion best practices and the knowledge context provided.
4. Assess the business impact severity.
5. Provide specific, actionable diagnostic steps an Oracle Fusion consultant should take.

Return your analysis as a JSON object matching the required schema.
Be precise. Do not fabricate information not present in the data.
"""


def build_order_rca_prompt(
    order_data: Dict[str, Any],
    knowledge_context: List[str],
    issue_description: Optional[str] = None,
) -> str:
    knowledge_block = "\n".join(f"- {k}" for k in knowledge_context) if knowledge_context else "No additional context retrieved."
    issue_block = f"\nReported Issue: {issue_description}" if issue_description else ""
    return f"""{SYSTEM_CONTEXT}

## TASK
Perform a Root Cause Analysis for the Oracle Fusion Order Management record below.{issue_block}

## ORDER DATA EXTRACTED FROM FUSION UI
```json
{_format_json(order_data)}
```

## RELEVANT KNOWLEDGE BASE CONTEXT
{knowledge_block}

## ANALYSIS INSTRUCTIONS
1. Review order header status, lines, orchestration status, fulfillment status.
2. Identify stuck orchestration steps, failed fulfillment lines, pricing errors, billing failures.
3. Check for missing configurations: pricing strategy, billing plan, revenue contract setup.
4. Assess orchestration process step failures and their downstream impact.
5. Provide specific next steps including SQL queries or UI navigation paths where applicable.

Return your analysis as a JSON object matching the required schema.
"""


def build_orchestration_rca_prompt(
    orchestration_data: Dict[str, Any],
    knowledge_context: List[str],
    issue_description: Optional[str] = None,
) -> str:
    knowledge_block = "\n".join(f"- {k}" for k in knowledge_context) if knowledge_context else "No additional context retrieved."
    issue_block = f"\nReported Issue: {issue_description}" if issue_description else ""
    return f"""{SYSTEM_CONTEXT}

## TASK
Perform a Root Cause Analysis for the Oracle Fusion Orchestration (DOO) process below.{issue_block}

## ORCHESTRATION DATA EXTRACTED FROM FUSION UI
```json
{_format_json(orchestration_data)}
```

## RELEVANT KNOWLEDGE BASE CONTEXT
{knowledge_block}

## ANALYSIS INSTRUCTIONS
1. Identify which orchestration step failed, is pending, or is blocked.
2. Determine if the failure is: integration error, missing setup, data validation failure, or system error.
3. Check process step dependencies and identify upstream/downstream impacts.
4. Provide specific steps to diagnose and remediate in Oracle Fusion DOO.

Return your analysis as a JSON object matching the required schema.
"""


def build_screenshot_analysis_prompt(module: str, context: str) -> str:
    return f"""{SYSTEM_CONTEXT}

## TASK
Analyze the attached Oracle Fusion screenshot from the {module.upper()} module.

## CONTEXT
{context}

## INSTRUCTIONS
1. Describe what you observe on the screen.
2. Identify any error messages, warning indicators, status values, or anomalies.
3. Extract key data points visible (record numbers, statuses, dates, amounts).
4. Assess if the observed state indicates a problem requiring investigation.
5. Suggest what additional pages/data should be reviewed.

Return your analysis as a JSON object matching the required schema.
"""


def _format_json(data: Dict[str, Any]) -> str:
    import json
    try:
        return json.dumps(data, indent=2, default=str)[:6000]  # Limit context size
    except Exception:
        return str(data)[:6000]
