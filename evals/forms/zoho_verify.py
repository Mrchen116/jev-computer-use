"""Host-side checks for the fixed synthetic invoice; not used to choose actions."""


def verify(observation):
    """Check all requested values and website-calculated totals."""
    values = {field["id"]: field["value"] for field in observation["fields"]}
    expected = {
        "address1": "Jev Demo Studio",
        "custName": "Demo Operator",
        "address2": "100 Example Avenue",
        "address3": "Example City",
        "companyCountry": "U.S.A",
        "billingAddress1": "Sample Client LLC",
        "billingAddress2": "200 Sample Street",
        "billingAddress3": "Sample City",
        "customerCountry": "U.S.A",
        "invNumber": "DEMO-20260923",
        "invoiceDate": "Sep 23, 2026",
        "dueDate": "Oct 23, 2026",
        "itemDesc.1": "Interface review",
        "itemDesc.2": "Documentation",
        "itemDesc.3": "Demo preparation",
        "customerNotes": "DEMONSTRATION ONLY - NOT PAYABLE",
        "terms": "Synthetic data for a software demonstration.",
        "currencySym": "$",
    }
    checks = {key: values.get(key) == value for key, value in expected.items()}
    for row, quantity, rate, amount in [
        (1, 2, 120, 240),
        (2, 3, 40, 120),
        (3, 1, 80, 80),
    ]:
        for field, expected_value in [
            ("itemQty", quantity),
            ("itemRate", rate),
            ("itemTax1", 0),
            ("itemTotal", amount),
        ]:
            key = f"{field}.{row}"
            try:
                checks[key] = float(values[key]) == expected_value
            except (KeyError, ValueError):
                checks[key] = False
    checks["website_total"] = observation["text"].count("440.00") == 2
    checks["three_populated_rows"] = (
        len(
            [
                key
                for key, value in values.items()
                if key.startswith("itemDesc.") and value
            ]
        )
        == 3
    )
    return {"passed": all(checks.values()), "checks": checks}
