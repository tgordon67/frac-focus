"""
Tests for Atlas product validation logic.

New simple rule:
- Supplier must contain 'atlas' (case insensitive)
- Product must match approved product list exactly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from atlas_product_analysis import AtlasProductAnalyzer


def test_atlas_validation():
    """Test simple Atlas validation: supplier contains 'atlas' + product in approved list."""
    analyzer = AtlasProductAnalyzer()

    print("=" * 80)
    print("TESTING SIMPLIFIED ATLAS VALIDATION")
    print("Rule 1: Supplier must contain 'atlas'")
    print("Rule 2: Product must be in approved list (exact match)")
    print("=" * 80)
    print()

    test_cases = [
        # (supplier, product, expected_result, description)

        # Case 1: Atlas supplier + approved product
        ("ATLAS SAND COMPANY", "SAND", True,
         "Atlas + 'SAND' → INCLUDE (in approved list)"),

        # Case 2: Atlas supplier + approved mesh size
        ("ATLAS SAND COMPANY", "40/70", True,
         "Atlas + '40/70' → INCLUDE (in approved list)"),

        # Case 3: Atlas supplier + approved 100 mesh
        ("ATLAS SAND COMPANY", "100 MESH", True,
         "Atlas + '100 MESH' → INCLUDE (in approved list)"),

        # Case 4: Atlas supplier + approved regional sand
        ("ATLAS ENERGY SOLUTIONS", "SAND - REGIONAL", True,
         "Atlas + 'SAND - REGIONAL' → INCLUDE (in approved list)"),

        # Case 5: Atlas supplier + approved Permian sand
        ("ATLAS SAND CO", "SAND, PERMIAN 40/140", True,
         "Atlas + 'SAND, PERMIAN 40/140' → INCLUDE (in approved list)"),

        # Case 6: Atlas supplier + approved West TX
        ("ATLAS SAND COMPANY LLC", "WEST TX 100 MESH", True,
         "Atlas + 'WEST TX 100 MESH' → INCLUDE (in approved list)"),

        # Case 7: Atlas supplier + approved silica sand
        ("ATLAS SAND", "SILICA SAND", True,
         "Atlas + 'SILICA SAND' → INCLUDE (in approved list)"),

        # Case 8: Atlas supplier + NOT in approved list
        ("ATLAS SAND COMPANY", "CERAMIC PROPPANT", False,
         "Atlas + 'CERAMIC PROPPANT' → EXCLUDE (not in approved list)"),

        # Case 9: Atlas supplier + NOT in approved list
        ("ATLAS SAND COMPANY", "RESIN COATED PROPPANT", False,
         "Atlas + 'RESIN COATED PROPPANT' → EXCLUDE (not in approved list)"),

        # Case 10: Atlas supplier + NOT in approved list
        ("ATLAS ENERGY SOLUTIONS", "CARBOLITE", False,
         "Atlas + 'CARBOLITE' → EXCLUDE (not in approved list)"),

        # Case 11: Non-Atlas supplier (missing 'atlas')
        ("SOME OTHER SAND COMPANY", "SAND", False,
         "Non-Atlas + 'SAND' → EXCLUDE (no 'atlas' in supplier)"),

        # Case 12: Non-Atlas supplier (missing 'atlas')
        ("US SILICA", "40/70", False,
         "Non-Atlas + '40/70' → EXCLUDE (no 'atlas' in supplier)"),

        # Case 13: Has 'atlas' in name + approved product
        ("atlas sand llc", "100 MESH", True,
         "lowercase 'atlas' + '100 MESH' → INCLUDE (contains 'atlas')"),

        # Case 14: Has 'ATLAS' in name + approved product
        ("SOME ATLAS COMPANY", "SAND", True,
         "'ATLAS' anywhere in name + 'SAND' → INCLUDE (contains 'atlas')"),

        # Case 15: Has 'atlas' but product not approved
        ("atlas company", "NORTHERN WHITE SAND", False,
         "Contains 'atlas' but product not in approved list → EXCLUDE"),

        # Case 16: Case insensitive product matching
        ("Atlas Energy", "sand", True,
         "Atlas + 'sand' (lowercase) → INCLUDE (case insensitive matching)"),
    ]

    passed = 0
    failed = 0

    for supplier, product, expected, description in test_cases:
        result = analyzer.is_valid_atlas_record(product, supplier)
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
    success = test_atlas_validation()
    sys.exit(0 if success else 1)
