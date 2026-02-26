# Microsoft Outlook Setup Guide

This guide walks through setting up Azure AD (Entra ID) app registration for Temporal Cortex to access Microsoft Outlook calendars. You will register an application in the Azure portal, configure API permissions, and authenticate the MCP server.

**Estimated time:** 10-15 minutes.

## Prerequisites

- A Microsoft account with Outlook Calendar (personal or work/school)
- Access to [Azure Portal](https://portal.azure.com/) (free — no Azure subscription required)
- Node.js 18+ installed (verify with `node --version`)
- A web browser for the OAuth consent flow

> **Note:** You do not need an Azure subscription or any paid Azure services. App registrations are available on the free tier of Azure Active Directory (now called Microsoft Entra ID).

## Step 1: Register an Application

1. Go to [Azure Portal](https://portal.azure.com/)
2. Search for "App registrations" in the top search bar (or navigate to **Microsoft Entra ID** > **App registrations**)
3. Click **+ New registration**
4. Fill in the registration form:
   - **Name**: A descriptive name (e.g., "Temporal Cortex MCP")
   - **Supported account types**: Choose based on your needs:
     - **Personal Microsoft accounts only** — for personal Outlook.com calendars
     - **Accounts in any organizational directory and personal Microsoft accounts** — for both work/school and personal calendars (recommended)
     - **Accounts in this organizational directory only** — for work/school calendars in your organization only
   - **Redirect URI**: Select **Public client/native (mobile & desktop)** and enter `http://localhost:8085/callback`
5. Click **Register**

You will be taken to the app's **Overview** page. Copy the **Application (client) ID** — this is your `MICROSOFT_CLIENT_ID`.

## Step 2: Create a Client Secret

1. In the left sidebar, click **Certificates & secrets**
2. Click **+ New client secret**
3. Enter a description (e.g., "Temporal Cortex MCP Secret")
4. Choose an expiry period:
   - **6 months** or **12 months** for personal use
   - **24 months** maximum
5. Click **Add**

Copy the **Value** column immediately — this is your `MICROSOFT_CLIENT_SECRET`. The value is only shown once; if you navigate away, you will need to create a new secret.

> **Important:** Do not confuse the **Value** with the **Secret ID**. You need the **Value** (the long string), not the UUID-format Secret ID.

## Step 3: Configure API Permissions

1. In the left sidebar, click **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Search for and select these permissions:
   - `Calendars.ReadWrite` — Read and write user calendars
   - `User.Read` — Sign in and read user profile (usually added by default)
6. Click **Add permissions**

> **Why Calendars.ReadWrite?** This single permission covers listing calendars, reading events, and creating events. Microsoft Graph does not have separate read-only calendar listing permissions in the delegated model.

### Optional: Admin Consent (Work/School Accounts Only)

If you are using a work or school account, some permissions may require admin consent:

7. Click **Grant admin consent for [Your Organization]** (only visible to directory admins)
8. Confirm the consent dialog

For personal Microsoft accounts, admin consent is not required — the user grants consent during the OAuth flow.

## Step 4: Configure the MCP Server

Set the credentials in your MCP client configuration file.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "temporal-cortex": {
      "command": "npx",
      "args": ["-y", "@temporal-cortex/cortex-mcp"],
      "env": {
        "MICROSOFT_CLIENT_ID": "your-application-client-id",
        "MICROSOFT_CLIENT_SECRET": "your-client-secret-value",
        "TIMEZONE": "America/New_York"
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
        "MICROSOFT_CLIENT_ID": "your-application-client-id",
        "MICROSOFT_CLIENT_SECRET": "your-client-secret-value",
        "TIMEZONE": "America/New_York"
      }
    }
  }
}
```

> **Multi-provider:** You can set both Google and Microsoft credentials to connect both providers simultaneously. The MCP server discovers all configured providers on startup.

## Step 5: Authenticate

Run the auth command for Outlook:

```bash
npx @temporal-cortex/cortex-mcp auth outlook
```

Or use the guided setup wizard:

```bash
npx @temporal-cortex/cortex-mcp setup
```

The auth flow will:

1. Start a temporary local HTTP server on port 8085
2. Open your browser to the Microsoft login page
3. After you sign in and authorize, Microsoft redirects back to the local server
4. The server exchanges the authorization code for access and refresh tokens
5. Tokens are stored at `~/.config/temporal-cortex/credentials.json`

After authentication, tokens refresh automatically in the background.

## Step 6: Verify

Restart your MCP client and ask:

> "List my calendars."

The agent should call `list_calendars` and return your Outlook calendars with provider-prefixed IDs like `outlook/Calendar` or `outlook/work`.

## Required Permissions Summary

| Permission | Type | Purpose |
|-----------|------|---------|
| `Calendars.ReadWrite` | Delegated | List calendars, read events, create events |
| `User.Read` | Delegated | Sign in and read basic profile |

## Troubleshooting

### "AADSTS700016: Application not found"

The `MICROSOFT_CLIENT_ID` is incorrect or the app registration was deleted. Verify the Application (client) ID in [Azure Portal](https://portal.azure.com/) > **App registrations** > your app > **Overview**.

### "AADSTS7000218: The request body must contain client_secret"

The `MICROSOFT_CLIENT_SECRET` is missing or incorrect. Verify:

1. You copied the **Value** (not the Secret ID) from **Certificates & secrets**
2. The secret has not expired (check the expiry date in the Azure Portal)
3. The environment variable is set correctly in your MCP client config

### "AADSTS65001: The user or administrator has not consented"

The required API permissions have not been consented to. For personal accounts, re-run `auth outlook` to trigger the consent prompt. For work/school accounts, ask your Azure AD admin to grant admin consent for the permissions.

### "AADSTS50011: The redirect URI does not match"

The redirect URI in the app registration does not match the one used by the auth flow. Verify:

1. Go to **App registrations** > your app > **Authentication**
2. Under **Platform configurations**, confirm there is a **Mobile and desktop applications** platform
3. The redirect URI should be `http://localhost:8085/callback`
4. If the port differs, update it to match your `OAUTH_REDIRECT_PORT` setting

### "Invalid client secret provided"

The client secret has expired. Go to **Certificates & secrets** in the Azure Portal, create a new secret, and update `MICROSOFT_CLIENT_SECRET` in your MCP client config.

### Calendar not appearing after auth

If `list_calendars` does not show your Outlook calendars:

1. Verify the auth succeeded by checking `~/.config/temporal-cortex/credentials.json` for a Microsoft entry
2. Ensure the calendar has events (empty calendars may still appear but with no events)
3. Check that the correct account was authorized (personal vs. work/school)

### Work/school account blocked by organization

Your organization's IT admin may have restricted third-party app access. Contact your admin to:

1. Allowlist the Application (client) ID in **Enterprise applications**
2. Grant admin consent for the `Calendars.ReadWrite` permission
3. Alternatively, use the **Accounts in this organizational directory only** account type and have the admin register the app

## Revoking Access

To disconnect Temporal Cortex from your Microsoft account:

**Personal accounts:**
1. Go to [Microsoft Account Security](https://account.live.com/consent/Manage)
2. Find your app and click **Remove**

**Work/school accounts:**
1. Go to [My Apps](https://myapps.microsoft.com/)
2. Find the app and revoke access
3. Or ask your Azure AD admin to remove the enterprise application

Then delete local credentials:

```bash
rm ~/.config/temporal-cortex/credentials.json
```

## Next Steps

- [Configuration Guide](configuration-guide.md) — timezone, week start, multi-calendar setup, all environment variables
- [First Run Guide](first-run-guide.md) — getting started in 5 minutes
- [Google Calendar Setup](google-cloud-setup.md) — add Google as an additional provider
- [CalDAV Setup](caldav-setup.md) — add iCloud, Fastmail, or other CalDAV providers
