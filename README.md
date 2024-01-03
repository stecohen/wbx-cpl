# Commands utilies for Webex Compliance Officers

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
# list messages sent by a user (default from = 30 days ago, default to = today)
python -m wbx_cpl user-messages user1@customer.com 

# list messages sent by a user and save in CSV file  
python -m wbx_cpl -c msgs.csv user-messages user1@customer.com 

# list messages sent by user between <from> and <to> dates  
python3 -m wbx_cpl user-messages -f '{"from":"2022-10-20T00:00:00.000Z", "to":"2023-10-20T00:00:00.000Z" }' user1@customer.com 

# list messages in a space, limit to 5 messages per user  
python3 -m wbx_cpl space-messages -f '{"max":5}' <spaceid>

# list members of a space
python3 -m wbx_cpl space-members  list-space-members <spaceid>

```

## Notes:
- the --filter option follows the input parameters of [Webex Events End Point](https://developer.webex.com/docs/api/v1/events/list-events)