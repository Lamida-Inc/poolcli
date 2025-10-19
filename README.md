# 🌊 poolcli

A command-line interface for managing Bittensor subnet pool operations. poolcli simplifies wallet authentication, developer key management, and pool administration through an intuitive CLI.

## Features

- **Wallet Authentication**: Seamless Bittensor wallet integration with secure token management
- **Developer Key Management**: Create, list, and manage developer keys with invoice tracking
- **Pool Management**: Create, list, and inspect subnet pools
- **Session Management**: Automatic token caching and re-authentication support

## Installation

```bash
pip install poolcli
or
uv add poolcli
```

Or install from source:

```bash
git clone <repository-url>
cd poolcli
pip install -e .
```

### Requirements

- Python 3.10+

## Quick Start

### 1. Authenticate

```bash
poolcli auth login --wallet-name my_wallet
```

You'll be prompted for your hotkey (defaults to "default" if not specified).

### 2. View Your Wallets

```bash
poolcli wallet list
```

This displays all available coldkeys and their associated hotkeys with addresses.

### 3. Create a Developer Key

```bash
poolcli key create --wallet-name my_wallet
```

This command will:

- Authenticate with your wallet
- Create an invoice for a developer key
- Prompt for payment in TAO
- Optionally create a pool after successful payment

### 4. Create a Pool

```bash
poolcli pool create --wallet-name my_wallet
```

### 5. View Your Pools

```bash
poolcli pool list --wallet-name my_wallet
```

## Command Reference

### Authentication (`auth`)

Manage authentication and sessions.

#### `poolcli auth login`

Authenticate with your Bittensor wallet.

```bash
poolcli auth login \
  --wallet-name my_wallet \
  --hotkey default \
  --force  # Force re-authentication
```

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--hotkey`: Hotkey name (defaults to "default")
- `--backend-url`: Backend API URL
- `--force`: Force re-authentication even if a valid session exists

#### `poolcli auth status`

Check your current authentication status.

```bash
poolcli auth status --wallet-name my_wallet
```

#### `poolcli auth logout`

Clear all stored authentication tokens.

```bash
poolcli auth logout
```

### Key Management (`key`)

Manage developer keys and invoices.

#### `poolcli key create`

Create a new developer key invoice and optionally proceed with payment.

```bash
poolcli key create \
  --wallet-name my_wallet \
  --hotkey default \
```

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--hotkey`: Hotkey to use for the key (defaults to "default")
- `--backend-url`: Backend API URL
- `--force`: Force re-authentication

#### `poolcli key list`

List all developer keys for your wallet.

```bash
poolcli key list \
  --wallet-name my_wallet \
  --page 1 \
  --limit 15 \
  --status active
```

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--page`: Page number for pagination (default: 1)
- `--limit`: Number of keys per page (default: 15)
- `--status`: Filter by status: `active`, `expired`, or `unused`
- `--backend-url`: Backend API URL

#### `poolcli key invoice get`

Check the status of a specific invoice.

```bash
poolcli key invoice get <invoice-id> --wallet-name my_wallet
```

**Arguments:**

- `invoice-id`: The invoice ID to check

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--backend-url`: Backend API URL

### Pool Management (`pool`)

Manage your Bittensor subnet pools.

#### `poolcli pool create`

Create a new pool for your wallet.

```bash
poolcli pool create \
  --wallet-name my_wallet \
  --hotkey default \
```

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--hotkey`: Hotkey to use for the pool (defaults to "default")
- `--backend-url`: Backend API URL
- `--force`: Force re-authentication

#### `poolcli pool list`

List all pools for your wallet.

```bash
poolcli pool list \
  --wallet-name my_wallet \
  --page 1 \
  --limit 15
```

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--page`: Page number for pagination (default: 1)
- `--limit`: Number of pools per page (default: 15)
- `--backend-url`: Backend API URL
- `--force`: Force re-authentication

#### `poolcli pool show`

View detailed information about a specific pool.

```bash
poolcli pool show <pool-id> --wallet-name my_wallet
```

**Arguments:**

- `pool-id`: The pool ID to inspect

**Options:**

- `--wallet-name` (required): Your Bittensor wallet name
- `--backend-url`: Backend API URL

### Wallet Management (`wallet`)

Inspect your Bittensor wallets.

#### `poolcli wallet list`

Display all available coldkeys and their associated hotkeys with addresses.

```bash
poolcli wallet list
```

This command scans your wallet directory and displays public key information (no password required).

## Global Options

```bash
poolcli --version      # Show version and exit
poolcli --commands     # Show all available commands and exit
poolcli --help         # Show help message and exit
```

### Wallet Storage

Bittensor wallets are typically stored in `~/.bittensor/wallets/`. The wallet list command reads from this directory.

## Common Workflows

### Complete Setup Workflow

```bash
# 1. View available wallets
poolcli wallet list

# 2. Authenticate
poolcli auth login --wallet-name my_wallet

# 3. Create a developer key
poolcli key create --wallet-name my_wallet

# 4. Check key status
poolcli key list --wallet-name my_wallet --status active

# 5. Create a pool
poolcli pool create --wallet-name my_wallet

# 6. View your pools
poolcli pool list --wallet-name my_wallet
```

### Check Invoice Status

```bash
# Create invoice
poolcli key create --wallet-name my_wallet

# Check status later
poolcli key invoice get <invoice-id> --wallet-name my_wallet
```

## Development

### Installation for Development

```bash
git clone <repository-url>
cd poolcli
pip install -e ".[dev]"
```

## License

GNU GENERAL PUBLIC LICENSE Version 2

## Support

For issues, questions, or contributions, please create issue in github.

## See Also

- [Bittensor Documentation](https://docs.bittensor.com/)
- [Bittensor GitHub](https://github.com/opentensor/bittensor)
- [BetterTherapy Subnet](https://github.com/BetterTherapy/BetterTherapy-Subnet)
