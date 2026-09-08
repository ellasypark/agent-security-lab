"""Application-owned authorization, independent of model instructions."""
from dataclasses import dataclass

FIELDS = {
    "read_email": {"email_id"},
    "save_draft": {"email_id", "body"},
    "send_email": {"email_id", "to", "body"},
}

@dataclass(frozen=True)
class Scope:
    email_id: str = "email_001"
    allowed_tools: frozenset[str] = frozenset({"read_email", "save_draft"})

def validate(name, args):
    if not isinstance(name, str) or name not in FIELDS:
        return "Unknown tool"
    if not isinstance(args, dict) or set(args) != FIELDS[name]:
        return "Invalid argument fields"
    if any(not isinstance(value, str) or not value or len(value) > 10000
           for value in args.values()):
        return "Invalid argument values"
    return None

def authorize(name, args, scope):
    error = validate(name, args)
    if error:
        return error
    if name not in scope.allowed_tools:
        return "Tool not authorized for this task"
    if args["email_id"] != scope.email_id:
        return "Email outside task scope"
    return None
