# Sysmon API documentation

## List system checks
`GET` `/checks`

### Response
`application/json`

As a response, a list of check results is being returned.
```json
{
  "$id": "https://homeinfo.de/system-checks.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a person, company, organization, or place",
  "type": "array",
  "items": {
    "type": "string"
  }
}
```
Each check result follows the following format:
```json
{
  "$id": "https://homeinfo.de/check-results.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "A representation of a person, company, organization, or place",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "The check record's ID."
    },
    "timestamp": {
      "type": "string",
      "description": "The timestamp of when the record was taken.."
    },
    "system": {
      "type": "System",
      "description": "The system that has been checked."
    },
    "icmpRequest": {
      "type": "boolean",
      "description": "The check result of the ICMP echo request."
    },
    "sshLogin": {
      "type": "string",
      "description": "The check result of the SSH login test."
    },
    "httpRequest": {
      "type": "string",
      "description": "The check result of the HTTP info request."
    },
    "applicationState": {
      "type": "string",
      "description": "The state of the digital signage application."
    },
    "smartCheck": {
      "type": "string",
      "description": "The check result of the last SMART checks."
    },
    "baytrailFreeze": {
      "type": "string",
      "description": "The check result of the Baytrail freeze vulnerability."
    },
    "applicationVersion": {
      "type": "string",
      "description": "The version of the application on the system."
    },
    "ramTotal": {
      "type": "integer",
      "description": "The amount of total RAM on the system in kilobytes."
    },
    "ramFree": {
      "type": "integer",
      "description": "The amount of free RAM on the system in kilobytes."
    },
    "ramAvailable": {
      "type": "integer",
      "description": "The amount of available RAM on the system in kilobytes."
    }
  }
}
```
