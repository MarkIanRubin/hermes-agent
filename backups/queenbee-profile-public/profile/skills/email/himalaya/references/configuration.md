# Himalaya Configuration Reference

Configuration file location: `~/.config/himalaya/config.toml`

## Minimal IMAP + SMTP Setup

```toml
[accounts.default]
email = "[REDACTED]"
display-name = "Your Name"
default = true

# IMAP backend for reading emails
backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "[REDACTED_EMAIL]"
backend.auth.type = "[REDACTED]"
backend.auth.raw = "[REDACTED]"

# SMTP backend for sending emails
message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "[REDACTED_EMAIL]"
message.send.backend.auth.type = "[REDACTED]"
message.send.backend.auth.raw = "[REDACTED]"
```

## Password Options

### Raw password (testing only, not recommended)

```toml
backend.auth.raw = "[REDACTED]"
```

### Password from command (recommended)

```toml
backend.auth.cmd = "[REDACTED]"
# backend.auth.cmd = "security find-generic-password -a [REDACTED_EMAIL] -s imap -w"
```

### System keyring (requires keyring feature)

```toml
backend.auth.keyring = "[REDACTED]"
```

Then run `himalaya account configure <account>` to store the password.

## Gmail Configuration

```toml
[accounts.gmail]
email = "[REDACTED]"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "[REDACTED_EMAIL]"
backend.auth.type = "[REDACTED]"
backend.auth.cmd = "[REDACTED]"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.gmail.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "[REDACTED_EMAIL]"
message.send.backend.auth.type = "[REDACTED]"
message.send.backend.auth.cmd = "[REDACTED]"
```

**Note:** Gmail requires an App Password if 2FA is enabled.

## iCloud Configuration

```toml
[accounts.icloud]
email = "[REDACTED]"
display-name = "Your Name"

backend.type = "imap"
backend.host = "imap.mail.me.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "[REDACTED_EMAIL]"
backend.auth.type = "[REDACTED]"
backend.auth.cmd = "[REDACTED]"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.mail.me.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "[REDACTED_EMAIL]"
message.send.backend.auth.type = "[REDACTED]"
message.send.backend.auth.cmd = "[REDACTED]"
```

**Note:** Generate an app-specific password at appleid.apple.com

## Folder Aliases

Map custom folder names:

```toml
[accounts.default.folder.alias]
inbox = "INBOX"
sent = "Sent"
drafts = "Drafts"
trash = "Trash"
```

## Multiple Accounts

```toml
[accounts.personal]
email = "[REDACTED]"
default = true
# ... backend config ...

[accounts.work]
email = "[REDACTED]"
# ... backend config ...
```

Switch accounts with `--account`:

```bash
himalaya --account work envelope list
```

## Notmuch Backend (local mail)

```toml
[accounts.local]
email = "[REDACTED]"

backend.type = "notmuch"
backend.db-path = "~/.mail/.notmuch"
```

## OAuth2 Authentication (for providers that support it)

```toml
backend.auth.type = "[REDACTED]"
backend.auth.client-id = "[REDACTED]"
backend.auth.client-secret.cmd = "[REDACTED]"
backend.auth.access-token.cmd = "[REDACTED]"
backend.auth.refresh-token.cmd = "[REDACTED]"
backend.auth.auth-url = "[REDACTED]"
backend.auth.token-url = "[REDACTED]"
```

## Additional Options

### Signature

```toml
[accounts.default]
signature = "Best regards,\nYour Name"
signature-delim = "-- \n"
```

### Downloads directory

```toml
[accounts.default]
downloads-dir = "~/Downloads/himalaya"
```

### Editor for composing

Set via environment variable:

```bash
export EDITOR="vim"
```
