# Wbx-cpl : commands utilies for Webex Compliance Officers

## Usage:
```
Usage: python -m wbx-cpl [OPTIONS] COMMAND [ARGS]...
       python -m wbx-cpl COMMAND --help 

Options:
  -t, --token TEXT     Your access token. Read from AUTH_BEARER env variable
                       by default.
  -d, --debug INTEGER  debug level.
  --help               Show this message and exit.

Commands:
  download-msg-files  Download files attached to given message id
  space-members       List emails of members in given space ID
  space-messages      List messages in by given space ID, up to 1000 messages per user
  user-messages       List messages sent by given user email, up to 1000 messages
```

# Examples:
```
# list messages sent by a user (default from = 30 days ago, default to = today)
python -m wbx-cpl user-messages user1@customer.com 

# list messages sent by a user and save in CSV file  
python -m wbx-cpl -c msgs.csv user-messages user1@customer.com 

# list messages sent by user between <from> and <to> dates  
python3 -m wbx-cpl user-messages -f '{"from":"2022-10-20T00:00:00.000Z", "to":"2023-10-20T00:00:00.000Z" }' user1@customer.com 

# list members of a space  
python3 -m wbx-cpl space-members co list-space-members <spaceid>

```

## Notes:
- the --filter option follows the input parameters of [Webex Events End Point](https://developer.webex.com/docs/api/v1/events/list-events)