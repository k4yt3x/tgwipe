# tgwipe

Wipe all of your messages from a Telegram group for everyone.

Log in once with your phone, point it at a group, and it deletes every message you've sent there using the [Telethon](https://github.com/LonamiWebs/Telethon) MTProto client.

## Setup

```bash
uv sync
```

## Usage

```bash
# Interactive — prompts for group on first run, phone + login code on first auth
uv run python -m tgwipe

# Specify the group up front
uv run python -m tgwipe --group @mygroup

# Preview only — count without deleting
uv run python -m tgwipe --group @mygroup --dry-run
```

The session is saved to `tgwipe.session` after the first login, so subsequent runs skip the SMS code.

## AI Use Declaration

AI tools were used to assist the design and implementation of this project. All design decisions were made by humans, and every change was reviewed and approved by a human maintainer.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).\
Copyright 2026 K4YT3X.
