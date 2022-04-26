# Sysmon API documentation
This documentation provides information about the web API of Sysmon.
The base URL for requests to this API is `https://sysmon.homeinfo.de`.
The endpoints listed below are, if not specified otherwise, relative to 
that URL.

## List system checks
`GET` `/checks`

### Response
`application/json`

As a response, an object of type
`https://jsonschema.homeinfo.de/sysmon/checked-systems.schema.` is returned.

## Run live check on a system
`GET` `/check/<int:system>`

### Response
`application/json`

As a response, an object of type
`https://jsonschema.homeinfo.de/sysmon/check-results.schema.`
is returned.

## Get a screenshot of a system
`GET` `/screenshot/<int:system>`

### Response
`image/jpeg`

As a response, a JPEG image is returned.

## Get checks view for customers
`GET` `/enduser`

### Response
`application/json`

As a response, an object of type
`https://jsonschema.homeinfo.de/sysmon/check-results-list.schema.json`
is returned