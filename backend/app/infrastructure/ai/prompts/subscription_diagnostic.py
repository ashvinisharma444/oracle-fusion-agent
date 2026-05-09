"""Subscription-specific diagnostic prompt."""
from __future__ import annotations

import json
from typing import Any, Dict

from app.infrastructure.ai.prompts.rca_analysis import RCA_RESPONSE_SCHEMA


def build_subscription_prompt(
    page_data: Dict[str, Any],
    knowledge_context: str,
    subscription_number: str,
) -> str:
    return f"""Analyze Oracle Fusion Subscription Management data for subscription {subscription_number}.

## Subscription Data
```json
{json.dumps(page_data, indent=2, default=str)[:8000]}
```

## Relevant Knowledge Context
{knowledge_context[:3000] if knowledge_context else "None available."}

## Diagnostic Focus Areas for Subscriptions
Examine for these common Oracle Subscription Management issues:
1. **Status Anomalies**: Subscription stuck in PENDING, SUSPENDED, or ERROR state
2. **Billing Issues**: Missing charges, incorrect billing account linkage, billing frequency errors
3. **Product Configuration**: Product code mismatches, service start/end date conflicts
4. **Auto-Renewal Problems**: Auto-renew flag misconfiguration, renewal failure patterns
5. **Integration Failures**: OSM to Billing (BRM) integration errors, event processing failures
6. **Entitlement Issues**: Service entitlement not activated post-subscription creation

## Required Response Schema
{json.dumps(RCA_RESPONSE_SCHEMA, indent=2)}

Provide a thorough RCA specific to Oracle Subscription Management. Return ONLY valid JSON.
"""
