# Error Codes Reference

## Overview

The API uses standard HTTP status codes to indicate success or failure.

## HTTP Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | The request succeeded |
| 201 | Created | The resource was created |

### Client Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request syntax |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

## Error Response Format



## Common Error Codes

### invalid_request
**HTTP Status**: 400 Bad Request
**Description**: The request is missing required parameters.

### rate_limited
**HTTP Status**: 429 Too Many Requests
**Description**: API rate limit exceeded.

### server_error
**HTTP Status**: 500 Internal Server Error
**Description**: An unexpected error occurred on the server.
