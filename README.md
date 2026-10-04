 # Art Suggestion Bot

 A small Telegram bot for collecting art and video suggestions and publishing them to a Telegram channel.

 The bot acts as a **suggestion inbox with moderation**: users send photos or videos to the bot, and the bot either publishes them immediately (for trusted users) or forwards them to the owner for approval.

 The project is written in Python with AI assistance and uses [Pyrofork](<https://github.com/Mayuri-Chan/pyrofork>) for Telegram interaction and SQLite for persistent state.

 ## Features

- Accepts photo and video suggestions.
- Supports Telegram media groups (albums).
- Preserves captions when reposting media.
- Checks whether the sender is a member of the target channel.
- Allows trusted users to bypass moderation.
- Sends untrusted suggestions to the owner for manual review.
- Provides **Approve** and **Reject** buttons for the owner.
- Allows the owner to provide a rejection reason, which is sent back to the submitter.
- Stores pending suggestions in SQLite.
- Provides `/allow` and `/disallow` commands for managing trusted users.
- Can run as a regular Python application.
- Includes a Nix flake with:
  - a development shell,
  - a Nix package,
  - a NixOS systemd service module.

 ## How it works

 The general workflow looks like this:

```
User
  │
  │ sends photo/video
  ▼
Telegram Bot
  │
  ├── Is the user a member of the channel?
  │       │
  │       └── No → reject the suggestion
  │
  ├── Is the user trusted?
  │       │
  │       ├── Yes → post directly to the channel
  │       │
  │       └── No
  │            │
  │            ├── Save suggestion to SQLite
  │            ├── Send suggestion to owner
  │            └── Wait for approval
  │
  ├── Approve → post to channel
  │
  └── Reject → ask owner for a reason
                    │
                    └── send reason to the user
```

 ### Trusted users

 Trusted users are stored in the SQLite database.

 When a trusted user sends a suggestion, the bot posts it to the configured channel immediately without asking the owner for approval.

 The owner can manage this list with:

```
/allow USER_ID
/disallow USER_ID
```

 For example:

```
/allow 123456789
```

 Only the configured `OWNER_ID` can use these commands.

 ### Regular users

 For users who are not on the trusted list:

1. The bot receives the photo/video.
2. The suggestion is saved to SQLite.
3. The owner receives a notification containing the suggestion ID.
4. The owner receives the actual media.
5. The owner can press **Yes** or **No**.
6. If approved, the media is posted to the channel.
7. If rejected, the owner is asked to provide a reason.
8. The reason is sent to the user.

 ## Requirements

 For a normal installation you need:

- Python 3
- `pip`
- Internet access
- A Telegram bot token
- Telegram API ID and API hash
- A Telegram channel where the bot can publish posts

 The Python dependencies are:

```
pyrotgfork
tgcrypto-pyrofork
python-dotenv
```

 They are listed in `requirements.txt`.

 ## Telegram configuration

 The bot requires both a **Telegram application API ID/API hash** and a **bot token**.

 ### API ID and API hash

 Create a Telegram application through Telegram's official API development tools:

 https://my.telegram.org

 After logging in, open **API development tools** and create an application. Telegram will provide an `api_id` and `api_hash`.

 See the official Telegram documentation for details:

 https://core.telegram.org/api/obtaining_api_id

 ### Bot token

 Create a bot through Telegram's **@BotFather**.

 Use `/newbot` and follow the instructions. BotFather will provide a token for the new bot.

 Keep the token secret: anyone who obtains it can control the bot.

 Official Telegram documentation:

 https://core.telegram.org/bots

 ## Environment variables

 The application reads its configuration from a `.env` file using `python-dotenv`.

 Create a `.env` file in the project directory:

```
API_ID=12345678
API_HASH=0123456789abcdef0123456789abcdef
BOT_TOKEN=1234567890:your_bot_token
OWNER_ID=123456789
CHANNEL_ID=-1001234567890
```

 ### Configuration reference

 | Variable | Description |
| --- | --- |
| `API_ID` | Telegram application ID obtained from `my.telegram.org`. |
| `API_HASH` | Telegram application hash obtained together with `API_ID`. |
| `BOT_TOKEN` | Authentication token of the Telegram bot obtained from @BotFather. |
| `OWNER_ID` | Numeric Telegram user ID of the person who moderates suggestions and manages trusted users. |
| `CHANNEL_ID` | Numeric Telegram ID of the channel where approved suggestions are published. |

`API_ID`, `OWNER_ID`, and `CHANNEL_ID` are parsed as integers, so they must contain numeric values.

 For example:

```
OWNER_ID=123456789
CHANNEL_ID=-1001234567890
```

 Do **not** commit `.env` to Git.

 The repository already ignores `.env`, SQLite databases, Pyrogram session files, virtual environments, and Python cache files.

 ## Telegram permissions

 The bot needs access to the target channel.

 For normal operation, add the bot to the channel and give it administrator permissions required to publish posts.

 The bot also uses the channel to check whether a user is a member before accepting their suggestion.

 The `CHANNEL_ID` should normally be the numeric channel ID, for example:

```
-1001234567890
```

 ## Installation on a regular Linux distribution

 The bot can be run on Debian, Ubuntu, Fedora, Arch Linux, or another distribution with Python 3.

 ### 1\. Clone the repository

```
git clone https://github.com/Makaroshka1973/art-suggestion-bot.git
cd art-suggestion-bot
```

 ### 2\. Create a virtual environment

 On most Linux distributions:

```
python3 -m venv venv
```

 Activate it:

```
source venv/bin/activate
```

 If your distribution does not have the Python virtual-environment module installed, install the appropriate package first.

 For Debian/Ubuntu, for example:

```
sudo apt install python3 python3-venv
```

 ### 3\. Install dependencies

```
pip install -r requirements.txt
```

 ### 4\. Configure the bot

 Create `.env`:

```
nano .env
```

 Add:

```
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=123456789
CHANNEL_ID=-1001234567890
```

 ### 5\. Start the bot

```
python main.py
```

 You should see:

```
Bot started.
```

 The bot will then start listening for Telegram updates.

 ## Running manually on Linux

 After the initial setup, the bot can simply be started with:

```
cd /path/to/art-suggestion-bot
source venv/bin/activate
python main.py
```

 For a long-running deployment, using systemd or the provided NixOS module is recommended.

 ## Running with systemd on a regular Linux distribution

 A regular Linux installation can also use systemd.

 For example, create:

```
/etc/systemd/system/art-suggestion-bot.service
```

 with:

```
[Unit]
Description=Art Suggestion Telegram Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/art-suggestion-bot
EnvironmentFile=/opt/art-suggestion-bot/.env
ExecStart=/opt/art-suggestion-bot/venv/bin/python /opt/art-suggestion-bot/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

 Adjust `User`, `WorkingDirectory`, and the paths to match your installation.

 Then:

```
sudo systemctl daemon-reload
sudo systemctl enable --now art-suggestion-bot
```

 Check its status:

```
systemctl status art-suggestion-bot
```

 View logs:

```
journalctl -u art-suggestion-bot -f
```

 ## Nix / NixOS

 The repository includes a `flake.nix`, so Nix users do not have to manually recreate the Python environment.

 The flake provides:

 - a development shell,
- a packaged executable called `art-suggestion-bot`,
- a NixOS module with a systemd service.

 The flake currently builds the required Pyrofork/TGCrypto packages itself and provides Python with `pyrotgfork`, `tgcrypto`, and `python-dotenv`.

 ### Development shell

 With Nix flakes enabled:

```
git clone https://github.com/Makaroshka1973/art-suggestion-bot.git
cd art-suggestion-bot

nix develop
```

 This enters a shell containing the Python environment required by the project.

 You can then run:

```
python main.py
```

 with a `.env` file in the project directory.

 ### Build the package

 The flake exposes the bot as its default package:

```
nix build
```

 Run the resulting executable with:

```
./result/bin/art-suggestion-bot
```

 You still need to provide the environment variables through `.env` or the environment.

 ## NixOS service

 The recommended NixOS deployment uses the module included in `flake.nix`.

 Add the repository as a flake input in your NixOS configuration.

 For example:

```
{
  inputs.art-suggestion-bot.url = "github:Makaroshka1973/art-suggestion-bot";

  outputs = { self, nixpkgs, art-suggestion-bot, ... }:
    {
      nixosConfigurations.my-host = nixpkgs.lib.nixosSystem {
        modules = [
          art-suggestion-bot.nixosModules.default

          {
            services.art-suggestion-bot = {
              enable = true;
              environmentFile = "/etc/art-suggestion-bot.env";
            };
          }
        ];
      };
    };
}
```

 Create the environment file:

```
/etc/art-suggestion-bot.env
```

 For example:

```
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=123456789
CHANNEL_ID=-1001234567890
```

 Then rebuild the system:

```
sudo nixos-rebuild switch --flake /path/to/your/flake#my-host
```

 The module creates a systemd service automatically.

 Check it with:

```
systemctl status art-suggestion-bot
```

 and view logs with:

```
journalctl -u art-suggestion-bot -f
```

 ### NixOS state directory

 The provided NixOS module uses:

```
StateDirectory = "art-suggestion-bot";
```

 The application reads the `STATE_DIRECTORY` environment variable and uses it as its state directory.

 Consequently, the SQLite database and Pyrogram state are stored in the service's managed state directory rather than in the source tree.

 This is useful for immutable/NixOS-style deployments because the application source can remain part of the Nix store while writable application state is kept separately.

 ## Database

 The bot uses SQLite.

 The database file is:

```
offerbot.sqlite3
```

 and is stored inside the configured state directory.

 By default:

```
STATE_DIRECTORY=.
```

 so when the bot is launched manually, the database is created in the current working directory.

 The database contains two tables.

 ### `allowed_users`

 Contains Telegram user IDs that are allowed to publish suggestions without moderation.

```
user_id INTEGER PRIMARY KEY
```

 ### `pending_offers`

 Contains suggestions waiting for owner approval.

 The table stores:

- offer ID,
- submitting user's ID,
- media information,
- caption.

 Media itself is **not downloaded and stored locally**. The bot stores Telegram `file_id` values and reuses them when publishing the suggestion.

 ## Media handling

 The bot accepts:

- photos,
- videos,
- photo/video albums.

 For albums, Telegram's `media_group_id` is used to collect the complete media group before processing it.

 The caption is taken from the first available caption in the group and attached to the first media item when the album is reposted.

 This means the bot does not need to download the submitted media to disk.

 ## Owner commands

 Only the configured owner can use the administration commands.

 ### `/allow`

 Add a user to the trusted list:

```
/allow 123456789
```

 The user will be able to submit posts without manual approval.

 ### `/disallow`

 Remove a user from the trusted list:

```
/disallow 123456789
```

 The user will return to the normal moderation workflow.

 ## Rejection workflow

 When the owner rejects a suggestion, the bot asks the owner to provide a reason.

 The next text message sent by the owner is treated as the rejection reason for the oldest pending rejection.

 For example:

```
❌ Your suggestion #42 was declined.

Reason: Please send a higher-resolution version.
```

 If several suggestions are rejected before reasons are provided, their reasons are handled as a queue.

 ## Project structure

```
art-suggestion-bot/
├── main.py
├── db.py
├── config.py
├── requirements.txt
├── flake.nix
├── flake.lock
├── LICENSE
└── .gitignore
```

 ### `main.py`

 The main application and Telegram handlers.

 Responsible for:

- starting Pyrofork,
- receiving photos and videos,
- handling albums,
- checking channel membership,
- checking trusted users,
- posting approved suggestions,
- notifying the owner,
- handling approval/rejection buttons,
- handling owner commands,
- sending rejection reasons.

 ### `db.py`

 SQLite persistence layer.

 Responsible for:

- initializing the database,
- adding/removing trusted users,
- checking whether a user is trusted,
- storing pending suggestions,
- retrieving pending suggestions,
- deleting processed suggestions.

 ### `config.py`

 Loads configuration from environment variables using `python-dotenv`.

 It also defines the state directory:

```
STATE_DIR = os.environ.get("STATE_DIRECTORY", ".")
```

 This makes the same application work both as a regular local Python process and as a NixOS systemd service.

 ### `flake.nix`

 Nix packaging and deployment configuration.

 It defines:

- the Python environment,
- Pyrofork and TGCrypto packages,
- the default Nix package,
- a development shell,
- the NixOS service module.

 ## Important operational notes

 ### Suggestions are stored in SQLite

 Pending suggestions survive a bot restart because they are stored in SQLite.

 However, the **rejection-reason queue is kept only in memory**. If the bot is restarted while there are rejected suggestions waiting for reasons, that queue is lost.

 ### Trusted users bypass moderation

 Anyone added with:

```
/allow USER_ID
```

 will have their suggestions published immediately.

 Use this only for users you trust.

 ### The bot does not process arbitrary files

 The current implementation only registers handlers for photos and videos.

 Text-only messages are not treated as suggestions.

 ### The bot must be able to contact users

 Telegram bots cannot initiate a conversation with a user who has never interacted with the bot. Users should open the bot and send a message before the bot can send them notifications or rejection reasons.

 ### Keep secrets out of Git

 Never commit:

```
.env
```

 or expose your bot token.

 The repository already includes `.env` in `.gitignore`.

 ## Troubleshooting

 ### `ValueError` while starting

 Check that all numeric variables contain valid numbers:

```
API_ID=12345678
OWNER_ID=123456789
CHANNEL_ID=-1001234567890
```

 ### The bot starts but cannot post to the channel

 Make sure the bot has been added to the target channel and has sufficient administrator permissions to publish messages.

 Also verify that `CHANNEL_ID` points to the correct channel.

 ### Users cannot submit suggestions

 The bot checks whether the submitting user is a member of the configured channel.

 Make sure:

- `CHANNEL_ID` is correct;
- the bot can access the channel;
- the user is actually a member of that channel.

 ### The owner does not receive approval requests

 Check:

```
OWNER_ID=...
```

 The value must be the numeric Telegram user ID of the owner.

 Also check the bot logs:

```
journalctl -u art-suggestion-bot -f
```

 or, when running manually:

```
python main.py
```

 ### The bot loses its database after a restart

 When running manually, make sure you start the bot from a stable working directory.

 The database is created relative to `STATE_DIRECTORY`, which defaults to the current directory.

 For systemd/NixOS deployments, use a persistent state directory.

 ## Security

 The following values are secrets and should never be published:

- `BOT_TOKEN`
- `API_HASH`

 Treat the bot token like a password. Anyone who obtains it can control the bot.

 The `OWNER_ID` and `CHANNEL_ID` are not authentication secrets, but they still determine who controls moderation and where content is published.

 ## License

 This project is licensed under the **GNU General Public License v3.0**.

 See `LICENSE` for the full license text.

 ## Links

- Repository: https://github.com/Makaroshka1973/art-suggestion-bot
- Telegram Bot documentation: https://core.telegram.org/bots
- Telegram API documentation: https://core.telegram.org/api
- Telegram API ID/API hash: https://my.telegram.org
- Bot creation and management: https://t.me/BotFather
