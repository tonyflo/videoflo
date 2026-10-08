<p align="center"><img width="250" alt="videoflo logo" src="https://user-images.githubusercontent.com/6558850/115158541-81734400-a043-11eb-8097-a7ae42325ef0.png"></p>

# videoflo
Videoflo is series of Python scripts to help automate your YouTube video production workflow in DaVinci Resolve.

Not only will Videoflo eliminate many mundane aspects of video production, but it will also keep your projects organized throughout the entire process from the inception of an idea to a published upload.

For a complete tutorial on how to install and use Videoflo, go to [videoflo.app](https://videoflo.app).

# UPDATE 2022-08-06
My YouTube Data API quota of 150,000 queries per day was reached in just a couple hours due to an abusive user of videoflo. For this reason, I have removed videoflo from production. Uploading to YouTube will no longer work. Other features of videoflo will still work just fine. Sorry for the inconvenience.

## Planka setup (2.x)

VideoFlo now uses your self-hosted Planka instance instead of Trello. The same
commands, production stages, local folders, offline mode, and Resolve workflow
remain available. Python 3.7+ is required. Install the integration dependency:

```sh
python -m pip install requests
```

Keep your existing `[main]` and channel settings. Replace the `[trello]` section
with `[planka]` and set your instance URL (including a subpath if applicable):

```ini
[planka]
url = https://planka.example.com

[ttt]
name = Tony Teaches Tech
path = Tony Teaches Tech
framerate = 30
width = 1920
height = 1080
schedule = 1,3,5
# Optional: copy the board ID from your Planka board URL.
planka_board_id =
```

Use a Planka user with **editor membership on the board**, including when the
user is an administrator. On versions offering API keys, generate a user API key
in Planka and set it locally:

```sh
export PLANKA_API_KEY='your-api-key'
```

Alternatively, set `PLANKA_TOKEN` to a Planka access token. Older 2.x releases may
only support access tokens. Get one locally with `POST /api/access-tokens`, using
a JSON body with `emailOrUsername` and `password`; the response's `item` contains
the token. The [official API documentation](https://docs.planka.cloud/docs/api-reference/swagger-ui/)
explains authentication. Complete any required login steps such as terms
acceptance or MFA in Planka. A token tied to a browser's HTTP-only cookie is not
suitable here; use an API key or a token issued without `withHttpOnlyToken`.
Tokens can expire or be revoked; replace them when you receive a 401.

`api_key` or `token` may also be set under `[planka]`, but environment variables
avoid storing credentials in the tracked `settings.ini`. Never commit credentials.
VideoFlo does not store your Planka password and uses verified TLS by default.

Run:

```sh
python init.py -c ttt
```

If `planka_board_id` is empty, choose an existing board interactively. VideoFlo
saves this ID separately from the old Trello `board_id`. Initialization creates
missing stage lists and a **VideoFlo** custom-field group; rerunning it keeps
existing lists and fields. Planka 1.x is not supported.

| VideoFlo feature | Planka equivalent |
| --- | --- |
| Script → Film → Edit → Finish → Render → Upload → Scheduled | Named board lists |
| Video title / description / scheduled release | Card name / description / due date |
| Tags and hashtags | Task lists named `tags` and `hashtags`, one task per entry |
| Filename and render stats | `VideoFlo` board custom-field group |
| YouTube and Studio links | Link attachments |

All task names are used as tags regardless of whether they are checked, matching
the original workflow. Stats are stored as text because Planka custom-field
values are strings. Due dates are normalized to UTC; cards in archive/trash lists
do not extend the publishing schedule. Keep the `Scheduled` list active or closed
so its due dates remain part of that schedule. With no existing due dates,
VideoFlo retains its previous default of one week from today.

### Existing projects and Trello migration

This update connects VideoFlo to Planka; it does not import Trello boards.
If you already imported your cards into Planka, initialize the board and link each
local project to its corresponding Planka card:

```sh
python link-card.py 'Existing project folder' PLANKA_CARD_ID -c ttt
python sync.py -c ttt --dry-run
```

The card ID is in the Planka card URL. Linking validates board membership and
writes only the local `.planka-card` file. Old `.card` files are left intact and
ignored, so Trello IDs cannot accidentally be sent to Planka. You can preserve
existing card titles, descriptions, due dates, and task lists by linking them.
Review the dry run before syncing: as before, **sync moves cards to the local
`.stage` value**, so set that file to the desired stage first.

For projects without an existing Planka card, `sync.py` creates a card on the
configured board and uses its local stage. Offline changes retain the same flow:

```sh
python new-video.py 'My video' -c ttt --offline
python sync.py -c ttt --dry-run
python sync.py -c ttt
```

Board initialization must precede online creation/sync. A dry run does not create
cards, change remote stages, or write card IDs. Existing unlinked Planka cards
must be linked first to avoid creating duplicates.

### Validation

```sh
python -m unittest discover -s tests -v
```

The tests mock Planka's 2.x HTTP contract and cover scheduling, metadata, stage
moves, custom fields, link attachments, error handling, and offline sync. Live
Planka, Resolve, macOS Finder tags, and YouTube uploads require testing on your
own workstation. The existing YouTube API quota limitation described above still
applies; this change does not restore the retired shared YouTube credentials.
