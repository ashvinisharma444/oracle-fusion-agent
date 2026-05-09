"""
Seed the ChromaDB vector store with Oracle Fusion knowledge base documents.
Run once after setup: python scripts/ingest_knowledge.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Sample Oracle Fusion knowledge for each module
ORACLE_KNOWLEDGE = {
    "subscription": [
        "Oracle Fusion Subscription Management: A subscription in PENDING_ACTIVATION status means the activation order has been submitted but the fulfillment has not yet completed. Check the linked orchestration order for stuck steps.",
        "Subscription billing schedules require a valid billing account, payment method, and billing profile. Missing billing profile association is a common cause of billing failures.",
        "Revenue recognition for subscriptions follows ASC 606. Performance obligations must be properly configured in the Revenue Management module. Missing SSP (Standalone Selling Price) will block revenue recognition.",
        "Subscription termination orders must complete all reversal steps in DOO (Digital Order Orchestration). Stuck CANCEL_SUBSCRIPTION tasks indicate upstream billing or revenue contract issues.",
        "Auto-renewal subscriptions require the renewal terms to be set at the subscription profile level. If the renewal profile is missing, the subscription will expire without renewal.",
    ],
    "order": [
        "Oracle Fusion Order Management: Orders stuck in BOOKED status with no active orchestration process indicate the DOO process failed to launch. Check the order orchestration monitor for error details.",
        "Pricing failures in Order Management are typically caused by: missing pricing segment, inactive price list, or expired pricing agreement. Check the pricing engine logs in the Pricing Administration work area.",
        "Tax calculation failures (ORDER_HEADER_TAX_NOT_CALCULATED) occur when the party tax profile is missing or the tax configuration is incomplete for the ship-to address jurisdiction.",
        "Fulfillment line status AWAIT_SHIPPING indicates the pick-release has been completed but the shipment confirmation is pending. This is normal for physical goods with warehouse processing delays.",
        "Order Management integration with Subscription Management: When an order is created for a subscription product, the subscription module must process the activation before the order can progress to CLOSED.",
    ],
    "orchestration": [
        "Oracle DOO (Digital Order Orchestration): A task in WAIT status means the orchestration step is waiting for an external system response. Check the integration logs for the dependent system.",
        "Orchestration process ERRORED state with message 'SUBSCRIPTION_CREATION_FAILED' indicates the subscription module rejected the creation request. Common causes: duplicate subscription, invalid product, missing customer setup.",
        "Manual task completion in DOO: Use Manage Orchestration Orders to manually advance a stuck process step. This requires the Orchestration Manager privilege.",
        "DOO compensation tasks execute when a prior task fails to allow rollback. If compensation also fails, the order enters a SYSTEM_HOLD requiring manual intervention.",
        "Fulfillment line status transitions: ENTERED → AWAITING_BILLING_SETUP → AWAITING_RECEIPT_ACCEPTANCE → CLOSED. Each transition depends on the fulfillment system completing its task.",
    ],
    "billing": [
        "Oracle Fusion Billing: Invoice generation failures often indicate missing bill-to address, invalid payment terms, or inactive receivables transaction type configuration.",
        "Bill plans must have valid billing schedules with correct period types and billing frequencies. A billing schedule with no active periods will cause billing to skip without error.",
        "Revenue correction process: Use the Correct Revenue process in Revenue Management to fix incorrectly recognized revenue. This creates adjustment journal entries.",
        "Credit memo creation for subscription adjustments requires the original invoice to be in VALIDATED or APPROVED status.",
    ],
    "pricing": [
        "Oracle Fusion Pricing: Price list effectivity dates must cover the order date. An expired price list will cause 'No price found' errors during order pricing.",
        "Pricing segments are used to control which customers see which prices. If the customer is not in the correct pricing segment, they may receive incorrect pricing or no pricing.",
        "Discount lists override price list pricing. Check the discount list assignment on the customer account and ensure it is active for the transaction date.",
        "Tiered pricing requires volume bands to be configured without gaps. A missing tier band will cause pricing failures for quantities falling in the gap.",
    ],
}

SAMPLE_SQL_PATTERNS = [
    """-- Find stuck orchestration processes
SELECT fo.order_number, fp.process_name, fpt.task_name, fpt.status_code, fpt.error_message
FROM doo_fulfill_orders fo
JOIN doo_orchestration_processes fp ON fp.fulfill_order_id = fo.fulfill_order_id
JOIN doo_process_tasks fpt ON fpt.process_id = fp.process_id
WHERE fpt.status_code IN ('ERROR', 'WAIT', 'CANCELED')
AND fp.creation_date > SYSDATE - 7
ORDER BY fo.creation_date DESC;""",

    """-- Check subscription activation status
SELECT s.subscription_number, s.status_code, s.start_date, s.end_date,
       s.billing_account_id, bac.account_number as billing_account_number
FROM okc_k_headers_b s
LEFT JOIN hz_cust_accounts bac ON bac.cust_account_id = s.bill_to_customer_id
WHERE s.status_code NOT IN ('ACTIVE', 'CLOSED', 'CANCELED')
AND s.creation_date > SYSDATE - 30
ORDER BY s.creation_date DESC;""",

    """-- Identify pricing failures on orders
SELECT oh.order_number, ol.line_number, ol.ordered_item, 
       ol.unit_selling_price, ol.pricing_date, ol.status_code
FROM oe_order_headers_all oh
JOIN oe_order_lines_all ol ON ol.header_id = oh.header_id
WHERE ol.unit_selling_price IS NULL
AND oh.ordered_date > SYSDATE - 7;""",
]

async def main():
    from app.infrastructure.vector.chromadb_adapter import get_vector_store
    from app.config.settings import get_settings

    settings = get_settings()
    print("Connecting to ChromaDB...")
    vector_store = await get_vector_store()

    total = 0
    for module, docs in ORACLE_KNOWLEDGE.items():
        metadatas = [{"module": module, "source": "oracle_knowledge_base", "title": f"{module}_doc_{i}"} for i, _ in enumerate(docs)]
        count = await vector_store.ingest(
            collection_name=settings.CHROMADB_COLLECTION_ORACLE_DOCS,
            documents=docs,
            metadatas=metadatas,
        )
        total += count
        print(f"  ✓ {module}: {count} documents ingested")

    # SQL patterns
    sql_metas = [{"module": "general", "source": "sql_library", "title": f"sql_pattern_{i}"} for i in range(len(SAMPLE_SQL_PATTERNS))]
    count = await vector_store.ingest(
        collection_name=settings.CHROMADB_COLLECTION_SQL_PATTERNS,
        documents=SAMPLE_SQL_PATTERNS,
        metadatas=sql_metas,
    )
    total += count
    print(f"  ✓ sql_patterns: {count} documents ingested")
    print(f"\n✓ Total: {total} documents ingested into knowledge base")


if __name__ == "__main__":
    asyncio.run(main())
