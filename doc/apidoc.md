# Sysmon API documentation
This documentation provides information about the web API of Sysmon.
The base URL for requests to this API is `https://sysmon.homeinfo.de`.
The endpoints listed below are, if not specified otherwise, relative to 
that URL.

## List system checks
`GET` `/checks`

### Response
`application/json`

As a response, an object of the type
`https://homeinfo.de/checked-systems.schema.` is returned.