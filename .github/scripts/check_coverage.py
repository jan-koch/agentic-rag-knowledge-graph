#!/usr/bin/env python3
"""
Check code coverage threshold from coverage.xml file.
Used by GitHub Actions CI workflow.
"""
import sys
import xml.etree.ElementTree as ET


def main():
    threshold = 20.0

    try:
        tree = ET.parse("coverage.xml")
        root = tree.getroot()
        line_rate = float(root.attrib["line-rate"])
        coverage_pct = line_rate * 100

        print(f"Coverage: {coverage_pct:.2f}%")

        if coverage_pct < threshold:
            print(f"ERROR: Coverage {coverage_pct:.2f}% is below threshold of {threshold}%")
            sys.exit(1)
        else:
            print(f"✅ Coverage {coverage_pct:.2f}% meets threshold of {threshold}%")
            sys.exit(0)

    except FileNotFoundError:
        print("ERROR: coverage.xml not found")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse coverage.xml: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
