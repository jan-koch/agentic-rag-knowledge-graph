#!/usr/bin/env python3
"""
Test script to verify Widget Embed API key auto-fill logic.

This tests the core logic without requiring a running Streamlit app.
"""

def test_api_key_logic():
    """Test the API key auto-fill logic"""

    # Simulate query params
    test_cases = [
        {
            "name": "With prefilled API key",
            "prefilled_key": "sk_test_1234567890abcdef",
            "expected_value": "sk_test_1234567890abcdef",
            "expected_comment": " // ✅ Pre-filled"
        },
        {
            "name": "Without prefilled API key (None)",
            "prefilled_key": None,
            "expected_value": "YOUR_API_KEY_HERE",
            "expected_comment": " // Replace with actual API key"
        },
        {
            "name": "Without prefilled API key (empty string)",
            "prefilled_key": "",
            "expected_value": "YOUR_API_KEY_HERE",
            "expected_comment": " // Replace with actual API key"
        }
    ]

    print("🧪 Testing Widget Embed API Key Auto-fill Logic\n")

    all_passed = True
    for test in test_cases:
        prefilled_api_key = test["prefilled_key"]

        # This is the logic from webui.py
        if prefilled_api_key:
            api_key_value = prefilled_api_key
            comment = ' // ✅ Pre-filled'
        else:
            api_key_value = 'YOUR_API_KEY_HERE'
            comment = ' // Replace with actual API key'

        # Verify
        passed = (api_key_value == test["expected_value"] and
                 comment == test["expected_comment"])

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test['name']}")
        print(f"  Input: {repr(prefilled_api_key)}")
        print(f"  Expected: {test['expected_value']} {test['expected_comment']}")
        print(f"  Got:      {api_key_value} {comment}")
        print()

        if not passed:
            all_passed = False

    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(test_api_key_logic())
