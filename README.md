## Commands utilities for Webex Compliance Officers

## Usage:
```
Usage: python -m wbx_cpl [OPTIONS] COMMAND [ARGS]...
       python -m wbx_cpl COMMAND --help 

Options:
  --version            Show the version and exit.
  -t, --token TEXT     Your access token. AUTH_BEARER env variable by default.
                       You can find your personal token at
                       https://developer.webex.com/docs/getting-started.
  -d, --debug INTEGER  Debug level.
  --help               Show this message and exit.

Commands:
  download-msg-files  Download files attached to given message ID.
  space-members       List emails of members in given space ID.
  space-messages      List messages in given space ID.
  user-messages       List (up to 1000) messages sent by given user email.
```

# Examples:
```

# List recordings 
python3 -m wbx_cpl  recordings -c /tmp/recs.csv -f '{"from":"2024-01-15T00:00:00.000Z","max":1}' sandbox.webex.com

# get recording details
python3 -m wbx_cpl  recording-details 34d9c6fdcaab453f8b540643e04b0830

# list user sent messages 
python3 -m wbx_cpl user-messages bc@cust1.onmicrosoft.com 

# list up to 5 user sent messages with space title (longer processing time) 
python3 -m wbx_cpl user-messages -t -f '{"max":5}' bc@cust1.onmicrosoft.com 

# list user messages and save to file 
python3 -m wbx_cpl user-messages -c /tmp/messages.csv bc@cust1.onmicrosoft.com 

# list user messages with tilte and save to file 
python3 -m wbx_cpl user-messages -c /tmp/messagesTitles.csv -t -f '{"max":5}' bc@cust1.onmicrosoft.com 

# list messages in space and save to file, up to 5 messages per user 
python3 -m wbx_cpl space-messages -c /tmp/spacemessages.csv -f '{"max":5}'  

# list all users in a in space, save to file 
python3 -m wbx_cpl space-members -c /tmp/members.csv <spaceid> 

# Download files attached to message id, save files under /tmp 
python3 -m wbx_cpl download-msg-files -d /tmp/ <spacid>
```

## Notes:
- the --filter option follows the input parameters of [Webex Events End Point](https://developer.webex.com/docs/api/v1/events/list-events)