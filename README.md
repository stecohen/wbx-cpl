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
  meeting
  messaging
  recording
```

# Examples:
```
# MEETING
# -------
# List messages sent in any meeting in Feb 2024 by given user email.
# python3 -m wbx_cpl meeting user_messages -f '{"from":"2024-02-01T00:00:00.000Z","to":"2024-02-29T20:26:59.814Z"} bc@4bfzj5.onmicrosoft.com

# List meeting participants in given meeting ID
# python3 -m wbx_cpl meeting participants 9fb5d46867f74d2ca91b1fabdff2e7b9_I_284366187397123659

# list messages posted in meeting given meeting ID, save in CSV file
# python3 -m wbx_cpl meeting messages -c /tmp/meeting-messages.csv 9fb5d46867f74d2ca91b1fabdff2e7b9_I_284366187397123659


# RECORDING
# ---------
# List recordings in given webex site from 15th Feb 2024. limit results to 5 recording
# python3 -m wbx_cpl recording list -c /tmp/recs.csv -f {"from":"2024-02-15T00:00:00.000Z","max":5} stephane-gaxe7-sandbox.webex.com

# Get recording details from given recording ID
# python3 -m wbx_cpl recording details 34d9c6fdcaab453f8b540643e04b0830

# Get recording contents from given recording ID
# python3 -m wbx_cpl recording download 34d9c6fdcaab453f8b540643e04b0830

# Get recording contents from recording IDs in .CSV input file
# python3 -m wbx_cpl recording download ./test-data/recording-input-list.csv

# MESSAGING
# ---------
# List user messages posted in any space in Feb 2024
# python3 -m wbx_cpl messaging user-messages -f {"from":"2024-02-01T00:00:00.000Z","to":"2024-02-29T20:26:59.814Z"} bc@4bfzj5.onmicrosoft.com

# List user messages, add space title and save to file
# python3 -m wbx_cpl messaging user-messages -c /tmp/messagesTitles.csv -t -f {"from":"2024-02-01T00:00:00.000Z","to":"2024-02-29T20:26:59.814Z"} bc@4bfzj5.onmicrosoft.com

# List messages posted in given space ID. Save to file, limit search to 5 messages per user.
# python3 -m wbx_cpl messaging space-messages -c /tmp/spacemessages.csv -f {"max":5} Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00vZjBhZTRjZDAtNTdhMS0xMWVlLWEyYjktYjU2MmFiZTI4YzY3

# List members in given space ID, save to file
# python3 -m wbx_cpl messaging space-members -c /tmp/members.csv Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00vZjBhZTRjZDAtNTdhMS0xMWVlLWEyYjktYjU2MmFiZTI4YzY3

# Download files attached to message id, save files under /tmp
# python3 -m wbx_cpl messaging message-files -d /tmp/ Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL01FU1NBR0UvMWYwY2NkZDAtYTNmMi0xMWVlLWI4ZGQtM2RlYzU4YzM1NTJm

```

## Notes:
- the --filter option follows the input parameters of [Webex Events End Point](https://developer.webex.com/docs/api/v1/events/list-events)