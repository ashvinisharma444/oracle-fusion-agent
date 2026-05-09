"""Order Management diagnostic prompt."""
from __future__ import annotations

import json
from typing import Any, Dict

from app.infrastructure.ai.prompts.rca_analysis import RCA_RESPONSE_SCHEMA


def build_order_prompt(
    page_data: Dict[str, Any],
    knowledge_context: str,
    order_number: str,
) -> str:
    return f"""Analyze Oracle Fusion Order Management data for order {order_number}.

## Order Data
```json
{json.dumps(page_data, indent=2, default=str)[:8000]}
```

## Relevant Knowledge Context
{knowledge_context[:3000] if knowledge_context else "None available."}

## Diagnostic Focus Areas for Orders
Examine for these common Oracle Order Management issues:
1. **Order Holds**: Price hold, credit check hold, availability hold — check hold reason codes
2. **Orchestration Failures**: DOO orchestration process errors, step failures, routing issues
3. **Fulfillment Errors**: Inventory reservation failures, pick/pack/ship exceptions
4. **Pricing Errors**: Price list not found, pricing rules not applied, charge calculation errors
5. **Scheduling Issues**: Requested ship date vs. scheduled ship date conflicts
6. **Integration Errors**: OM to WMS, OM to AR (billing), OM to SCM integration failures
7. **Line Item Issues**: Lines in error status, quantity mismatches, unit of measure problems

## Required Response Schema
{json.dumps(RCA_RESPONSE_SCHEMA, indent=2)}

Provide a thorough RCA specific to Oracle Order Management. Return ONLY valid JSON.
"""
