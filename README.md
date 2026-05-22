# portwatch

> Small daemon that monitors open ports and alerts on unexpected changes via webhook or email.

---

## Installation

```bash
pip install portwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/portwatch.git && cd portwatch && pip install .
```

---

## Usage

Create a configuration file `portwatch.yml`:

```yaml
interval: 60  # seconds between scans
alerts:
  webhook: "https://hooks.example.com/notify"
  email: "ops@example.com"
ignored_ports:
  - 22
  - 80
  - 443
```

Start the daemon:

```bash
portwatch --config portwatch.yml
```

Run a one-shot scan without daemonizing:

```bash
portwatch --config portwatch.yml --once
```

When an unexpected port opens or closes, portwatch fires an alert to your configured webhook or email with details about the change, the process owning the port, and a timestamp.

---

## Configuration Options

| Key | Description | Default |
|---|---|---|
| `interval` | Scan interval in seconds | `60` |
| `ignored_ports` | Ports to silently skip | `[]` |
| `alerts.webhook` | Webhook URL for notifications | `null` |
| `alerts.email` | Email address for notifications | `null` |

---

## License

MIT © 2024 Your Name