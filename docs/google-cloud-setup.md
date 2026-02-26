# Google Calendar Setup Guide

This guide walks through setting up Google OAuth credentials for Temporal Cortex. You will create a Google Cloud project, enable the Calendar API, create OAuth credentials, and authenticate the MCP server.

**Estimated time:** 10-15 minutes.

## Prerequisites

- A Google account with Google Calendar enabled
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Node.js 18+ installed (verify with `node --version`)
- A web browser for the OAuth consent flow

> **Tip:** If you have not used Google Cloud Console before, you may need to accept the Terms of Service on your first visit. No billing account is required for this setup.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** in the top navigation bar
3. Click **New Project** in the dialog that appears
4. Enter a project name (e.g., "Temporal Cortex Calendar")
5. Leave the **Organization** and **Location** fields at their defaults (or select your organization if applicable)
6. Click **Create**
7. Wait for the notification confirming the project was created, then click **Select Project** (or use the project selector to switch to it)

> **Verify:** The project name should appear in the top navigation bar next to "Google Cloud".

## Step 2: Enable the Google Calendar API

1. In your new project, navigate to **APIs & Services** > **Library** (or use the search bar to search for "Google Calendar API")
2. Search for "Google Calendar API"
3. Click on **Google Calendar API** in the results
4. Click **Enable**
5. Wait for the API to be enabled (this takes a few seconds)

> **Verify:** After enabling, you should see the Google Calendar API dashboard with "API Enabled" status. The "Disable" button confirms it is active.

## Step 3: Configure the OAuth Consent Screen

The consent screen is what users see when they authorize the app to access their calendar.

1. Navigate to **APIs & Services** > **OAuth consent screen**
2. Select the user type:
   - **External** — choose this unless you have a Google Workspace organization and want to restrict access to your domain
   - **Internal** — only available for Google Workspace; restricts to users in your organization
3. Click **Create**
4. Fill in the required fields on the **App information** page:
   - **App name**: A descriptive name (e.g., "My Calendar Assistant" or "Temporal Cortex MCP")
   - **User support email**: Your email address
   - **App logo**: Optional (skip for personal use)
   - **App domain**: Optional (skip for personal use)
   - **Developer contact email**: Your email address
5. Click **Save and Continue**

### Add Calendar Scopes

6. On the **Scopes** page, click **Add or Remove Scopes**
7. In the filter, search for "Google Calendar"
8. Select these two scopes:
   - `https://www.googleapis.com/auth/calendar` — See, edit, share, and permanently delete all the calendars you can access using Google Calendar
   - `https://www.googleapis.com/auth/calendar.events` — View and edit events on all your calendars
9. Click **Update** to confirm the scopes
10. Click **Save and Continue**

> **Why two scopes?** The `calendar` scope allows listing calendars and reading metadata. The `calendar.events` scope allows reading and writing events. Both are required for full Temporal Cortex functionality (listing calendars, reading events, booking).

### Add Test Users

11. On the **Test users** page, click **Add Users**
12. Enter your Google email address (the one associated with the calendar you want to access)
13. Click **Add**
14. Click **Save and Continue**

> **Important:** While the app is in "Testing" status, only users listed as test users can authorize it. You can add up to 100 test users. To remove this restriction, you would need to go through Google's app verification process (not required for personal use).

15. On the **Summary** page, review your settings and click **Back to Dashboard**

## Step 4: Create OAuth 2.0 Credentials

1. Navigate to **APIs & Services** > **Credentials**
2. Click **+ Create Credentials** at the top of the page
3. Select **OAuth client ID** from the dropdown
4. For **Application type**, select **Desktop app**
5. Enter a name (e.g., "Temporal Cortex MCP")
6. Click **Create**

A dialog will display your **Client ID** and **Client Secret**:
- **Client ID** looks like: `123456789-abcdefghijk.apps.googleusercontent.com`
- **Client Secret** looks like: `GOCSPX-AbCdEfGhIjKlMnOpQrStUv`

> **Important:** Copy both values immediately or click **Download JSON** to save the credentials file. Google shows the Client Secret only at creation time. You can always regenerate a new secret later, but the original cannot be retrieved.

## Step 5: Configure the MCP Server

You have two options for providing credentials to the MCP server.

### Option A: Environment Variables (Recommended)

Set the credentials in your MCP client configuration file:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "temporal-cortex": {
      "command": "npx",
      "args": ["-y", "@temporal-cortex/cortex-mcp"],
      "env": {
        "GOOGLE_CLIENT_ID": "123456789-abcdef.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "GOCSPX-your-secret-here"
      }
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "temporal-cortex": {
      "command": "npx",
      "args": ["-y", "@temporal-cortex/cortex-mcp"],
      "env": {
        "GOOGLE_CLIENT_ID": "123456789-abcdef.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "GOCSPX-your-secret-here"
      }
    }
  }
}
```

### Option B: JSON Credentials File

1. On the Credentials page, click the download icon next to your OAuth client
2. Save the JSON file to a secure location (e.g., `~/.config/temporal-cortex/google-credentials.json`)
3. Set the path as an environment variable in your MCP client config:

```json
{
  "env": {
    "GOOGLE_OAUTH_CREDENTIALS": "/Users/yourname/.config/temporal-cortex/google-credentials.json"
  }
}
```

The server reads `installed.client_id` and `installed.client_secret` from the standard Google Cloud Console JSON format automatically.

> **Security note:** Do not commit the credentials file to version control. Add it to your `.gitignore` if it is inside a project directory.

## Step 6: Authenticate

Run the auth command to complete the OAuth flow:

```bash
npx @temporal-cortex/cortex-mcp auth google
```

Or use the guided setup wizard which handles auth, timezone, and client configuration:

```bash
npx @temporal-cortex/cortex-mcp setup
```

**Docker alternative:**

```bash
docker run --rm -it \
  -e GOOGLE_CLIENT_ID="your-id" -e GOOGLE_CLIENT_SECRET="your-secret" \
  -p 8085:8085 \
  -v ~/.config/temporal-cortex:/root/.config/temporal-cortex \
  cortex-mcp auth google
```

The auth flow will:

1. Start a temporary local HTTP server on port 8085 (configurable via `OAUTH_REDIRECT_PORT`)
2. Open your default web browser to the Google OAuth consent screen
3. After you authorize, Google redirects back to the local server with an authorization code
4. The server exchanges the code for access and refresh tokens (using PKCE for security)
5. Tokens are stored at `~/.config/temporal-cortex/credentials.json`
6. The interactive setup prompts you to confirm your timezone, week start day, and telemetry preference

After authentication, the MCP server reuses stored tokens automatically. Tokens refresh in the background when they expire — you should not need to re-authenticate unless you revoke access.

## Step 7: Verify

Restart your MCP client and ask:

> "List my calendars."

The agent should call `list_calendars` and return your Google Calendar list with provider-prefixed IDs like `google/primary`.

## Troubleshooting

### "Access blocked: This app's request is invalid"

Your OAuth consent screen may not be configured correctly. Check:

1. **Test user added** — Go to **OAuth consent screen** > **Test users** and verify your Google email is listed
2. **Calendar API enabled** — Go to **APIs & Services** > **Library** and confirm the Google Calendar API shows "Enabled"
3. **Correct scopes** — Go to **OAuth consent screen** > **Scopes** and verify both calendar scopes are listed
4. **Application type** — The OAuth client must be "Desktop app" (not "Web application")

### "Port 8085 is already in use"

Another application is using the default OAuth callback port. Set a different port:

```bash
OAUTH_REDIRECT_PORT=9090 npx @temporal-cortex/cortex-mcp auth google
```

Or set it in your MCP client config:

```json
{
  "env": {
    "OAUTH_REDIRECT_PORT": "9090"
  }
}
```

### "The redirect URI in the request does not match"

This error occurs when using a "Web application" OAuth client instead of a "Desktop app" client. Web app clients require pre-registered redirect URIs, while Desktop app clients accept any `localhost` redirect. Create a new OAuth client with type "Desktop app".

### "invalid_grant" or "Token has been expired or revoked"

The stored refresh token is no longer valid. This can happen if:

- You revoked the app's access in [Google Account permissions](https://myaccount.google.com/permissions)
- The refresh token expired (Google tokens expire after 7 days if the app is in "Testing" status and hasn't been verified)
- You changed your Google password

**Fix:** Re-run the auth flow:

```bash
npx @temporal-cortex/cortex-mcp auth google
```

### "Error 403: access_denied"

The user attempting to authorize is not listed as a test user. Go to **OAuth consent screen** > **Test users** and add their email address. Alternatively, submit the app for verification to allow any Google user to authorize.

### Browser does not open automatically

If running in a headless environment (SSH, Docker without display), the auth flow will print the authorization URL to the terminal. Copy the URL and open it in a browser on any machine. After authorizing, the browser will redirect to `localhost:8085` — if that machine is not the same one running the MCP server, you will need to copy the redirect URL and open it on the server machine.

### Google Workspace admin restrictions

If your organization's Google Workspace admin has restricted third-party app access, you may see "This app is blocked". Contact your admin to allowlist the OAuth Client ID, or use an **Internal** OAuth consent screen type if you have admin access.

## Revoking Access

To disconnect Temporal Cortex from your Google Calendar:

1. Go to [Google Account permissions](https://myaccount.google.com/permissions)
2. Find your app name (e.g., "My Calendar Assistant")
3. Click **Remove Access**
4. Delete the local credentials: `rm ~/.config/temporal-cortex/credentials.json`

## Next Steps

- [Configuration Guide](configuration-guide.md) — timezone, week start, multi-calendar setup, all environment variables
- [First Run Guide](first-run-guide.md) — getting started in 5 minutes
- [Outlook Setup](outlook-setup.md) — add Microsoft Outlook as an additional provider
- [CalDAV Setup](caldav-setup.md) — add iCloud, Fastmail, or other CalDAV providers
