from __future__ import annotations

import sys

from src.config import load_settings
from src.commands import CommandRouter


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python run_command.py "command string"')
        return

    cmd = sys.argv[1]
    settings = load_settings()
    router = CommandRouter(confirmation_required=settings.command_confirmation)
    result = router.route(cmd)
    print('Handled:', result.handled)
    print('Response:', result.response)


if __name__ == '__main__':
    main()
