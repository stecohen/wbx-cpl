## Commands utilities for Webex Compliance Officers

## Usage:
```
Usage: 
  python -m wbx_cpl [OPTIONS] COMMAND [ARGS]...
  python -m wbx_cpl COMMAND --help 

Options:
  --version            Show the version and exit.
  -t, --token TEXT     Your access token. AUTH_BEARER env variable by default.
                       You can find your personal token at
                       https://developer.webex.com/docs/getting-started.
  -d, --debug INTEGER  Debug level.
  --help               Show this message and exit.

Commands:
  download-msg-files     Download files attached to given message ID.
  meeting-messages       List user messages posted in meeting ID.
  meeting-participants   List meeting participants of given meeting ID.
  meeting-user-messages  List (up to 1000) messages sent in meetings by...
  recording-details      Print detais of given recording ID.
  recordings             List recordings for given webex site
  space-members          List emails of members in given space ID.
  space-messages         List messages in given space ID.
  user-messages          List (up to 1000) messages sent by given user...
```

# Examples:
```
# List messages sent in meetings by given user email.
python -m wbx_cpl  meeting-user-messages bc@4bfzj5.onmicrosoft.com

# List meeting participants in given meeting ID.
python -m wbx_cpl  meeting-participants <meetingID>

# list messages posted in meeting given meeting ID, save in CSV file,
python -m wbx_cpl  meeting-messages -c /tmp/meeting-messages.csv <meetingID>

# List recordings in given webex site from 15th of Jan 2024. limit results to one recording.
python -m wbx_cpl  recordings -c /tmp/recs.csv -f {"from":"2024-01-15T00:00:00.000Z","max":1} stephane-gaxe7-sandbox.webex.com

# Get recording details from given recording ID.
python -m wbx_cpl  recording-details <recordingID>

# List messages posted by user email in any space.
python -m wbx_cpl  user-messages bc@4bfzj5.onmicrosoft.com

# list user messages, add space tite and save to file.
python -m wbx_cpl  user-messages -c /tmp/messagesTitles.csv -t -f {"max":5} bc@4bfzj5.onmicrosoft.com

# List messages posted in given space ID. Save to file, limit search to 5 messages per user.
python -m wbx_cpl  space-messages -c /tmp/spacemessages.csv -f {"max":5} <spaceID>

# List members in given space ID, save to file.
python -m wbx_cpl  space-members -c /tmp/members.csv <spaceID>

# Download files attached to message id, save files under /tmp.
python -m wbx_cpl  download-msg-files -d /tmp/ <messageID> 

```

## Notes:
- the --filter option follows the input parameters of [Webex Events End Point](https://developer.webex.com/docs/api/v1/events/list-events)