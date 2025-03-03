# Union Monitor Bot v1.0

Welcome to the first stable release of the Union Monitor Bot! This Telegram bot provides a hosted solution for monitoring validators on Tendermint-based blockchains (e.g., Union, Cosmos SDK chains). Instead of running complex software locally, users can interact with the bot via Telegram, configuring their validator details and receiving real-time alerts and insights.

## Key Features

- **Multi-User Support**: Register multiple validators using Telegram commands (`/register`, `/config`), with per-user configurations stored securely.
- **Validator Monitoring**: Tracks critical metrics like voting power, rank, jailed status, delegator count, uptime, and sync status.
- **Missed Blocks Alerts**: Monitors missed blocks within a configurable slashing window, with alerts triggered above a threshold (default: 10 blocks).
- **Graphing**: Visualize missed blocks over time with a sleek, black-background graph featuring an orange trend line (`/graph`).
- **Customizable Settings**: Adjust RPC/REST API endpoints, slashing window, and threshold via Telegram.
- **Hosted Convenience**: No local installation required—users interact directly with the bot hosted by the maintainers.

## How It Works

1. **Register**: Users start with `/register` to enable monitoring.
2. **Configure**: Set validator addresses and node endpoints with `/config` (e.g., `/config consensus_address=YOUR_ADDRESS rpc_url=http://your.node:26657`).
3. **Monitor**: Use commands like `/status`, `/missed`, `/network`, `/validator`, and `/graph` to get updates.
4. **Alerts**: Receive proactive Telegram notifications for critical events (e.g., validator jailed, high miss rate).

## Technical Details

- **Backend**: Built with Python 3.11, `aiohttp` for async API calls, and `python-telegram-bot` for Telegram integration.
- **Data Storage**: User configs in `users.json`, history in `history.json` (cleared on start/stop).
- **Dependencies**: `aiohttp`, `python-telegram-bot`, `matplotlib`, `python-dotenv`.
- **Deployment**: Runs as a `systemd` service, logging to `bot.log` and `bot.err`.

## Usage

- Add `@YourBotName` on Telegram (replace with your bot’s actual handle).
- Follow the setup with `/register` and `/config`.
- Enjoy real-time validator monitoring!

## Known Issues

- REST API endpoints (e.g., `/cosmos/slashing/v1beta1/signing_infos`) may fail on some nodes; the bot falls back to RPC block signature checks.
- Requires server-side hosting by the maintainer.

## Future Plans

- Add SQLite for scalable user data.
- Enhance security with admin controls or registration codes.
- Support additional metrics (e.g., proposer status).

## Contributions

This is an open-source project—fork it, tweak it, and submit pull requests! See the [README](README.md) for setup details if you want to host your own instance.

## Credits

Developed by eastwood_nft with support from xAI’s Grok.

---

**Release Notes**: Check out the [v1.0.0 release](https://github.com/yourusername/union-monitor/releases/tag/v1.0.0) for the full changelog and setup instructions.
