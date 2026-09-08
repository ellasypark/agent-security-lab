"""Run deterministic authorization demos or a live local-model experiment."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
from tools import Executor

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "ollama"], default="demo")
    parser.add_argument("--scenario", choices=["normal", "attack"], default="attack")
    parser.add_argument("--unguarded", action="store_true", help="Disable authorization for local comparison")
    parser.add_argument("--model", help="Installed Ollama model supporting tool calling")
    args = parser.parse_args()
    if args.mode == "ollama" and not args.model:
        parser.error("--model is required in ollama mode")
    output = Path("runs") / uuid4().hex
    executor = Executor(output, attack=args.scenario == "attack", guarded=not args.unguarded)
    if args.mode == "demo":
        print("SCRIPTED DEMO: injected tool requests, not evidence of model susceptibility.")
        executor.execute("read_email", {"email_id": "email_001"})
        if args.scenario == "attack":
            result = executor.execute("send_email", {"email_id": "email_001", "to": "audit@attacker.test", "body": "I can attend."})
        else:
            result = executor.execute("save_draft", {"email_id": "email_001", "body": "I can attend."})
        print(json.dumps(result, indent=2))
    else:
        from agent import run
        print(run(executor, args.model))
    print(f"Run artifacts: {output.resolve()}")

if __name__ == "__main__":
    main()
