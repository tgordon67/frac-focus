"""
Tests for Atlas product validation logic.

Tests the supplier-aware validation: if supplier field says "Atlas",
trust it and include products that Atlas is documented as producing.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from atlas_product_analysis import AtlasProductAnalyzer


def test_atlas_supplier_validation():
    """Test that Atlas supplier field is trusted for documented products."""
    analyzer = AtlasProductAnalyzer()

    print("=" * 80)
    print("TESTING ATLAS SUPPLIER-AWARE PRODUCT VALIDATION")
    print("=" * 80)
    print()

    test_cases = [
        # (supplier, product, expected_result, description)

        # Case 1: Atlas supplier + generic sand (should be INCLUDED)
        ("ATLAS SAND COMPANY", "SAND", True,
         "Atlas + generic 'SAND' → INCLUDE (trust supplier)"),

        # Case 2: Atlas supplier + specific mesh size (should be INCLUDED)
        ("ATLAS SAND COMPANY", "40/70", True,
         "Atlas + '40/70' → INCLUDE (documented Atlas product)"),

        # Case 3: Atlas supplier + 100 mesh (should be INCLUDED)
        ("ATLAS SAND COMPANY", "100 MESH", True,
         "Atlas + '100 MESH' → INCLUDE (documented Atlas product)"),

        # Case 4: Atlas supplier + regional sand (should be INCLUDED)
        ("ATLAS ENERGY SOLUTIONS", "SAND - REGIONAL", True,
         "Atlas + 'REGIONAL' → INCLUDE (documented Atlas product)"),

        # Case 5: Atlas supplier + Permian sand (should be INCLUDED)
        ("ATLAS SAND CO", "SAND, PERMIAN 40/140", True,
         "Atlas + 'PERMIAN' → INCLUDE (documented Atlas product)"),

        # Case 6: Atlas supplier + West TX (should be INCLUDED)
        ("ATLAS SAND COMPANY LLC", "WEST TX 100 MESH", True,
         "Atlas + 'WEST TX' → INCLUDE (documented Atlas product)"),

        # Case 7: Atlas supplier + generic but lazy entry (should be INCLUDED)
        ("ATLAS SAND", "SILICA SAND", True,
         "Atlas + 'SILICA SAND' → INCLUDE (trust supplier, generic sand)"),

        # Case 8: Atlas supplier + CERAMIC (should be EXCLUDED even with Atlas)
        ("ATLAS SAND COMPANY", "CERAMIC PROPPANT", False,
         "Atlas + 'CERAMIC' → EXCLUDE (Atlas doesn't make ceramic)"),

        # Case 9: Atlas supplier + RESIN COATED (should be EXCLUDED)
        ("ATLAS SAND COMPANY", "RESIN COATED PROPPANT", False,
         "Atlas + 'RESIN COATED' → EXCLUDE (Atlas doesn't make RCS)"),

        # Case 10: Atlas supplier + CARBOLITE (should be EXCLUDED)
        ("ATLAS ENERGY SOLUTIONS", "CARBOLITE", False,
         "Atlas + 'CARBOLITE' → EXCLUDE (Atlas doesn't make ceramic)"),

        # Case 11: Non-Atlas supplier + sand (should be EXCLUDED)
        ("SOME OTHER SAND COMPANY", "SAND", False,
         "Non-Atlas + 'SAND' → EXCLUDE (not Atlas supplier)"),

        # Case 12: Non-Atlas supplier + 40/70 (should be EXCLUDED)
        ("US SILICA", "40/70 MESH", False,
         "Non-Atlas + '40/70' → EXCLUDE (not Atlas supplier)"),

        # Case 13: Capital Sand (legacy Atlas brand) + product
        ("CAPITAL SAND", "40/140 BROWN", True,
         "Capital Sand + '40/140' → INCLUDE (Capital is Atlas legacy brand)"),

        # Case 14: Atlas subsidiary + product
        ("OLC KERMIT", "100 MESH", True,
         "OLC Kermit + '100 MESH' → INCLUDE (OLC Kermit is Atlas subsidiary)"),

        # Case 15: Atlas + Northern White (should be EXCLUDED even with Atlas)
        ("ATLAS SAND COMPANY", "SAND-PREMIUM WHITE-40/70", False,
         "Atlas + 'PREMIUM WHITE' → EXCLUDE (Atlas doesn't produce Northern White)"),
    ]

    passed = 0
    failed = 0

    for supplier, product, expected, description in test_cases:
        result = analyzer.is_valid_atlas_product_for_supplier(product, supplier)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}: {description}")
        print(f"  Supplier: {supplier}")
        print(f"  Product: {product}")
        print(f"  Expected: {expected}, Got: {result}")
        print()

    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = test_atlas_supplier_validation()
    sys.exit(0 if success else 1)
