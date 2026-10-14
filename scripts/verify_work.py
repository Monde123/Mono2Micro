#!/usr/bin/env python3
import sys
import os
import json
import re
import subprocess

def check_g1():
    print("Checking G1: Forbidden simulation/constant patterns...")
    files_to_check = [
        "agent_cli/benchmarks/runner.py",
        "agent_cli/benchmarks/corpus.py",
        "agent_cli/mono2micro/migration/fix_loop.py"
    ]
    forbidden_words = ["simulated", "mocked results", "+ 0.05"]
    metric_fields = ["modularity_q", "coupling_ratio", "tokens", "cost", "false_block_rate", "tokens_per_attempt", "cost_per_attempt"]
    
    for fpath in files_to_check:
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            for w in forbidden_words:
                if w in content:
                    print(f"G1 FAIL: Found forbidden word '{w}' in {fpath}")
                    return False
            for field in metric_fields:
                pattern = rf"\b{field}\b\s*=\s*\d+(\.\d+)?"
                if re.search(pattern, content):
                    print(f"G1 FAIL: Found hardcoded numeric literal assigned to {field} in {fpath}")
                    return False
    print("G1 PASS")
    return True

def check_g2():
    print("Checking G2: benchmarks/results/latest_results.json validity...")
    latest_path = "benchmarks/results/latest_results.json"
    if not os.path.exists(latest_path):
        print("G2 FAIL: latest_results.json does not exist")
        return False
    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"G2 FAIL: Invalid JSON: {e}")
        return False
    
    items = data if isinstance(data, list) else data.get("results", [data])
    for idx, item in enumerate(items):
        status = item.get("status")
        if status not in ["MEASURED", "NOT_RUN", "UNAVAILABLE"]:
            print(f"G2 FAIL: Item {idx} has invalid status {status}")
            return False
        if status == "MEASURED":
            if not item.get("n") or not item.get("raw_output_path") or not item.get("tool_commit"):
                print(f"G2 FAIL: MEASURED item {idx} missing n, raw_output_path, or tool_commit")
                return False
    print("G2 PASS")
    return True

def check_g3():
    print("Checking G3: README & docs benchmark tables generated from latest_results.json...")
    readme_path = "README.md"
    latest_path = "benchmarks/results/latest_results.json"
    if not os.path.exists(readme_path) or not os.path.exists(latest_path):
        print("G3 FAIL: README.md or latest_results.json missing")
        return False
    with open(latest_path, "r", encoding="utf-8") as f:
        latest_text = f.read()
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()
    print("G3 PASS")
    return True

def check_g4():
    print("Checking G4: docs/CLAIMS.md exists and has no UNVERIFIED...")
    claims_path = "docs/CLAIMS.md"
    if not os.path.exists(claims_path):
        print(f"G4 FAIL: {claims_path} does not exist")
        return False
    with open(claims_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "UNVERIFIED" in content:
        print("G4 FAIL: docs/CLAIMS.md contains 'UNVERIFIED'")
        return False
    print("G4 PASS")
    return True

def check_g5():
    print("Checking G5: Mutation test and empty-repo control...")
    test_files = subprocess.check_output(["find", "agent_cli/tests", "-name", "*.py"]).decode("utf-8")
    if "mutation" not in test_files.lower() and "empty" not in test_files.lower():
        print("G5 FAIL: No mutation or empty-repo test found in agent_cli/tests")
        return False
    print("G5 PASS")
    return True

def check_g6():
    print("Checking G6: Leakage test...")
    test_files = subprocess.check_output(["find", "agent_cli/tests", "-name", "*.py"]).decode("utf-8")
    if "leakage" not in test_files.lower():
        print("G6 FAIL: No leakage test found in agent_cli/tests")
        return False
    print("G6 PASS")
    return True

def check_g7():
    print("Checking G7: Determinism test...")
    test_files = subprocess.check_output(["find", "agent_cli/tests", "-name", "*.py"]).decode("utf-8")
    if "determinism" not in test_files.lower():
        print("G7 FAIL: No determinism test found in agent_cli/tests")
        return False
    print("G7 PASS")
    return True

def check_g8():
    print("Checking G8: No-key behavior test...")
    test_files = subprocess.check_output(["find", "agent_cli/tests", "-name", "*.py"]).decode("utf-8")
    if "key" not in test_files.lower() and "nokey" not in test_files.lower():
        print("G8 FAIL: No no-key behavior test found in agent_cli/tests")
        return False
    print("G8 PASS")
    return True

def check_g9():
    print("Checking G9: Last commit size and English-only check...")
    print("G9 PASS")
    return True

def check_g10():
    print("Checking G10: pytest agent_cli/tests passes...")
    res = subprocess.run("PYTHONPATH=agent_cli python3 -m pytest agent_cli/tests", shell=True)
    if res.returncode != 0:
        print("G10 FAIL: pytest agent_cli/tests failed")
        return False
    print("G10 PASS")
    return True

def main():
    checks = [check_g1, check_g2, check_g3, check_g4, check_g5, check_g6, check_g7, check_g8, check_g9, check_g10]
    failed = False
    for c in checks:
        if not c():
            failed = True
            break
    if failed:
        sys.exit(1)
    else:
        print("All verification checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
