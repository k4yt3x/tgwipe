import argparse
import asyncio
import sys

from loguru import logger
from telethon.tl.custom.message import Message

from tgwipe.cleaner import Cleaner

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

DEFAULT_SESSION = "tgwipe"
DEFAULT_PREVIEW = 10
PREVIEW_TEXT_LIMIT = 80


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete all of your messages from a Telegram group (for everyone).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--session",
        default=DEFAULT_SESSION,
        help="session file name to persist login",
    )
    parser.add_argument(
        "-g",
        "--group",
        help="group username, invite link, or numeric ID",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="count messages without deleting",
    )
    parser.add_argument(
        "-p",
        "--preview",
        type=int,
        default=DEFAULT_PREVIEW,
        help="show this many of the most recent messages before deleting (0 to disable)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="skip the deletion confirmation prompt",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    return parser.parse_args()


def log_preview(messages: list[Message], n: int) -> None:
    if n <= 0:
        return
    shown = messages[:n]
    logger.info(
        "This will delete the following messages ({} most recent of {:,} shown):",
        len(shown),
        len(messages),
    )
    for msg in shown:
        text = (msg.message or "").strip().replace("\n", " ")
        if not text:
            text = "[media]" if msg.media else "[empty]"
        if len(text) > PREVIEW_TEXT_LIMIT:
            text = text[: PREVIEW_TEXT_LIMIT - 3] + "..."
        ts = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "?"
        logger.info("  [{}] {}", ts, text)


def configure_logging(verbose: bool) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if verbose else "INFO",
        format="<green>{time:HH:mm:ss}</green> <level>{level:<8}</level> {message}",
    )


async def run(args: argparse.Namespace) -> int:
    async with Cleaner(API_ID, API_HASH, args.session) as cleaner:
        group_input = args.group or input("Group (username, link, or ID): ").strip()
        try:
            group = await cleaner.resolve_group(group_input)
        except Exception as e:
            logger.error("Could not resolve group: {}", e)
            return 1

        messages = await cleaner.collect_my_messages(group)
        if not messages:
            return 0

        log_preview(messages, args.preview)

        if args.dry_run:
            logger.info("Dry-run mode; nothing deleted")
            return 0

        if not args.yes:
            confirm = (
                input(f"Delete {len(messages):,} messages for everyone? [y/N] ")
                .strip()
                .lower()
            )
            if confirm not in ("y", "yes"):
                logger.info("Aborted")
                return 0

        await cleaner.delete_messages(group, [m.id for m in messages])
    return 0


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    try:
        sys.exit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()
