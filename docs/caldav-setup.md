# CalDAV Setup Guide

This guide walks through connecting CalDAV-based calendar providers to Temporal Cortex. CalDAV is an open standard (RFC 4791) supported by iCloud, Fastmail, Nextcloud, Radicale, and many other calendar servers.

Unlike Google and Outlook which use OAuth, CalDAV providers authenticate with a username and app-specific password (or regular password for self-hosted servers).

**Estimated time:** 5 minutes.

## Prerequisites

- Node.js 18+ installed (verify with `node --version`)
- A CalDAV-compatible calendar account (iCloud, Fastmail, Nextcloud, etc.)
- An app-specific password for your provider (see provider-specific sections below)

> **No environment variables needed.** CalDAV credentials are entered interactively during the auth flow and stored locally. You do not need to set any environment variables in your MCP client config for CalDAV.

## Quick Start

```bash
npx @temporal-cortex/cortex-mcp auth caldav
```

The interactive auth flow prompts for:

1. **Provider preset** — choose iCloud, Fastmail, or Custom
2. **Username** — your email or account username
3. **Password** — your app-specific password (not your regular account password for iCloud/Fastmail)
4. **CalDAV URL** — auto-filled for iCloud and Fastmail, manual entry for Custom

Credentials are stored at `~/.config/temporal-cortex/credentials.json`. The server discovers all CalDAV calendars on the account automatically.

Or use the guided setup wizard which handles auth, timezone, and client configuration:

```bash
npx @temporal-cortex/cortex-mcp setup
```

## Apple iCloud

### Step 1: Generate an App-Specific Password

Apple requires an app-specific password for third-party CalDAV access. Your regular Apple ID password will not work.

1. Go to [appleid.apple.com](https://appleid.apple.com/)
2. Sign in with your Apple ID
3. Navigate to **Sign-In and Security** > **App-Specific Passwords**
4. Click **Generate an app-specific password** (or the **+** button)
5. Enter a label (e.g., "Temporal Cortex")
6. Click **Create**
7. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)

> **Important:** Copy the password immediately. Apple does not show it again. If you lose it, you will need to generate a new one.

### Step 2: Authenticate

```bash
npx @temporal-cortex/cortex-mcp auth caldav
```

When prompted:
- **Provider**: Select **iCloud**
- **Username**: Your Apple ID email (e.g., `user@icloud.com`)
- **Password**: The app-specific password from Step 1

The CalDAV URL is auto-filled for iCloud: `https://caldav.icloud.com/`

### Step 3: Verify

Restart your MCP client and ask:

> "List my calendars."

You should see your iCloud calendars with provider-prefixed IDs like `caldav/Home`, `caldav/Work`, etc.

### iCloud Notes

- **Two-factor authentication** must be enabled on your Apple ID to generate app-specific passwords
- iCloud supports multiple calendars — all calendars on the account are discovered automatically
- Shared calendars (calendars shared with you by other users) appear as read-only
- App-specific passwords can be revoked individually at [appleid.apple.com](https://appleid.apple.com/) > **App-Specific Passwords**

## Fastmail

### Step 1: Generate an App-Specific Password

Fastmail requires an app-specific password for CalDAV access.

1. Log in to [Fastmail](https://www.fastmail.com/)
2. Go to **Settings** > **Privacy & Security** > **Integrations** (or navigate directly to **Settings** > **Passwords & Security** > **Third-party apps**)
3. Click **New App Password** (or **Add** under App Passwords)
4. Enter a name (e.g., "Temporal Cortex")
5. For **Access**, select **CalDAV** (or leave as **Full access** if CalDAV is not listed separately)
6. Click **Generate Password**
7. Copy the generated password

### Step 2: Authenticate

```bash
npx @temporal-cortex/cortex-mcp auth caldav
```

When prompted:
- **Provider**: Select **Fastmail**
- **Username**: Your Fastmail email (e.g., `user@fastmail.com`)
- **Password**: The app-specific password from Step 1

The CalDAV URL is auto-filled for Fastmail: `https://caldav.fastmail.com/dav/calendars/user/`

### Step 3: Verify

Restart your MCP client and ask:

> "List my calendars."

You should see your Fastmail calendars with provider-prefixed IDs like `caldav/Personal`, `caldav/Work`.

### Fastmail Notes

- Fastmail app passwords can have granular access scopes — CalDAV access is sufficient for Temporal Cortex
- Delegated calendars (from other Fastmail users) are discoverable if the delegation is configured in Fastmail settings
- App passwords can be managed at **Settings** > **Privacy & Security** > **Integrations**

## Custom CalDAV Server

For self-hosted or other CalDAV servers (Nextcloud, Radicale, Baikal, SOGo, Zimbra, etc.):

### Step 1: Gather Connection Details

You need three pieces of information:

| Detail | Description | Example |
|--------|-------------|---------|
| **CalDAV URL** | The CalDAV principal or base URL | `https://cloud.example.com/remote.php/dav/` |
| **Username** | Your account username | `user@example.com` |
| **Password** | Your account password or app password | `your-password` |

Common CalDAV URL patterns:

| Server | URL Pattern |
|--------|-------------|
| Nextcloud | `https://your-domain/remote.php/dav/` |
| Radicale | `https://your-domain/` |
| Baikal | `https://your-domain/dav.php/` |
| SOGo | `https://your-domain/SOGo/dav/` |
| Zimbra | `https://your-domain/dav/` |
| cPanel (Horde) | `https://your-domain:2080/` |

> **Tip:** If you are unsure of your CalDAV URL, check your server's documentation or look for CalDAV settings in the web interface. Many servers also support auto-discovery via `/.well-known/caldav`.

### Step 2: Authenticate

```bash
npx @temporal-cortex/cortex-mcp auth caldav
```

When prompted:
- **Provider**: Select **Custom**
- **CalDAV URL**: Enter your server's CalDAV URL
- **Username**: Your account username
- **Password**: Your account password (or app-specific password if your server supports them)

### Step 3: Verify

Restart your MCP client and ask:

> "List my calendars."

You should see your calendars with provider-prefixed IDs like `caldav/personal`, `caldav/shared`.

### Self-Hosted Notes

- **HTTPS required** — The MCP server rejects plain HTTP CalDAV URLs for security. If your server uses a self-signed certificate, you may need to configure certificate trust at the OS level.
- **Authentication** — Most self-hosted servers use HTTP Basic Auth. If your server requires digest auth or other methods, check your server documentation.
- **Calendar discovery** — The server uses CalDAV `PROPFIND` on the principal URL to discover all calendars. If no calendars are found, verify the CalDAV URL points to the correct principal (not a specific calendar).
- **Nextcloud app passwords** — Nextcloud supports app-specific passwords at **Settings** > **Security** > **Devices & sessions**. Using an app password is recommended over your account password.

## Multi-Provider Setup

CalDAV can be combined with Google Calendar and Microsoft Outlook. Run the auth flow for each provider you want to connect:

```bash
# Connect Google
npx @temporal-cortex/cortex-mcp auth google

# Connect Outlook
npx @temporal-cortex/cortex-mcp auth outlook

# Connect CalDAV (iCloud)
npx @temporal-cortex/cortex-mcp auth caldav
```

The server discovers all configured providers on startup and merges their calendars into a unified view. Use provider-prefixed IDs to target specific calendars:

- `google/primary` — Google Calendar primary calendar
- `outlook/Calendar` — Outlook default calendar
- `caldav/Home` — iCloud Home calendar

## Troubleshooting

### "Authentication failed" or "401 Unauthorized"

The username or password is incorrect. Verify:

1. You are using an **app-specific password** (not your regular account password) for iCloud and Fastmail
2. The password was copied correctly (no trailing spaces)
3. Two-factor authentication is enabled on your Apple ID (required for iCloud app-specific passwords)

### "No calendars found"

The CalDAV URL may not point to the correct principal. Try:

1. Check if your server supports auto-discovery: `https://your-domain/.well-known/caldav`
2. For Nextcloud, ensure the URL ends with `/remote.php/dav/` (not `/remote.php/dav/calendars/user/`)
3. Some servers require the full principal URL including your username (check server docs)

### "SSL certificate error" or "Connection refused"

For self-hosted servers:

1. Ensure your server uses HTTPS with a valid certificate (Let's Encrypt is free)
2. Check that the CalDAV port is accessible from your machine
3. If behind a firewall, verify the port is open

### iCloud: "Your Apple ID or password is incorrect"

- You must use an **app-specific password**, not your Apple ID password
- Ensure two-factor authentication is enabled at [appleid.apple.com](https://appleid.apple.com/)
- If you recently changed your Apple ID password, existing app-specific passwords may have been revoked — generate a new one

### Fastmail: "Authentication error"

- Verify the app password has CalDAV access enabled (check the app password's scope in Fastmail settings)
- Ensure you are using the email address (not username) as the CalDAV username

### CalDAV calendars not merging with Google/Outlook

All providers should appear in `list_calendars` output. If CalDAV calendars are missing:

1. Check `~/.config/temporal-cortex/credentials.json` for a CalDAV entry
2. Re-run `npx @temporal-cortex/cortex-mcp auth caldav` to re-authenticate
3. Verify `~/.config/temporal-cortex/config.json` lists the CalDAV provider

## Revoking Access

**iCloud:**
1. Go to [appleid.apple.com](https://appleid.apple.com/) > **Sign-In and Security** > **App-Specific Passwords**
2. Click the **x** next to the password you want to revoke, or click **Revoke All**

**Fastmail:**
1. Go to **Settings** > **Privacy & Security** > **Integrations**
2. Delete the app password

**Self-hosted:**
1. Delete or change the app password in your server's admin panel

Then delete local credentials:

```bash
rm ~/.config/temporal-cortex/credentials.json
```

## Next Steps

- [Configuration Guide](configuration-guide.md) — timezone, week start, multi-calendar setup, all environment variables
- [First Run Guide](first-run-guide.md) — getting started in 5 minutes
- [Google Calendar Setup](google-cloud-setup.md) — add Google as an additional provider
- [Outlook Setup](outlook-setup.md) — add Microsoft Outlook as an additional provider
