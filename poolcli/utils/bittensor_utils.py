import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bittensor_wallet import Wallet

from poolcli.utils.console import Console


# A simple dataclass to hold wallet names and addresses
@dataclass
class WalletInfo:
    name: str  # coldkey name
    path: str
    coldkey_address: Optional[str] = None  # SS58 address
    hotkeys: list[dict[str, Optional[str]]] = field(default_factory=list)  # (name, address)


class _Hotkey:
    def __init__(self, hotkey_ss58=None):
        self.ss58_address = hotkey_ss58


class _Coldkeypub:
    def __init__(self, coldkey_ss58=None):
        self.ss58_address = coldkey_ss58


class WalletLike:
    def __init__(
        self,
        name=None,
        hotkey_ss58=None,
        hotkey_str=None,
        coldkeypub_ss58=None,
    ):
        self.name = name
        self.hotkey_ss58 = hotkey_ss58
        self.hotkey_str = hotkey_str
        self._hotkey = _Hotkey(hotkey_ss58)
        self._coldkeypub = _Coldkeypub(coldkeypub_ss58)

    @property
    def hotkey(self):
        return self._hotkey

    @property
    def coldkeypub(self):
        return self._coldkeypub


def print_console(message: str, colour: str, title: str, console_: Console):
    console_.print(f"[bold {colour}][{title}]:[/bold {colour}] [{colour}]{message}[/{colour}]\n")


def get_wallet_path() -> Path:
    """
    Returns the default bittensor wallet path.
    """
    return Path.home() / ".bittensor" / "wallets"


def get_hotkey_pub_ss58(wallet: Wallet) -> str:
    """
    Helper fn to retrieve the hotkeypub ss58 of a wallet that may have been created before
    bt-wallet 3.1.1 and thus not have a wallet hotkeypub. In this case, it will return the hotkey
    SS58.
    """
    from bittensor.utils import KeyFileError
    try:
        return wallet.hotkeypub.ss58_address
    except (KeyFileError, AttributeError):
        return wallet.hotkey.ss58_address


def get_coldkey_wallet_from_path(path: str):
    """Get all coldkey wallet names from path."""
    try:
        wallet_names = next(os.walk(os.path.expanduser(path)))[1]
        return [Wallet(path=path, name=name) for name in wallet_names]
    except StopIteration:
        # No wallet files found.
        wallets = []
    return wallets


def get_hotkey_wallets_for_wallet(
    wallet: Wallet, show_nulls: bool = False, show_encrypted: bool = False
) -> list[Optional[Wallet]]:
    """
    Returns wallet objects with hotkeys for a single given wallet

    :param wallet: Wallet object to use for the path
    :param show_nulls: will add `None` into the output if a hotkey is encrypted or not on the device
    :param show_encrypted: will add some basic info about the encrypted hotkey

    :return: a list of wallets (with Nones included for cases of a hotkey being encrypted or not on the device, if
             `show_nulls` is set to `True`)
    """
    from bittensor.utils import KeyFileError
    hotkey_wallets = []
    wallet_path = Path(wallet.path).expanduser()
    hotkeys_path = wallet_path / wallet.name / "hotkeys"
    try:
        hotkeys = [entry.name for entry in hotkeys_path.iterdir()]
    except (FileNotFoundError, NotADirectoryError):
        hotkeys = []
    for h_name in hotkeys:
        if h_name.endswith("pub.txt"):
            if h_name.split("pub.txt")[0] in hotkeys:
                continue
            else:
                hotkey_for_name = Wallet(
                    path=str(wallet_path),
                    name=wallet.name,
                    hotkey=h_name.split("pub.txt")[0],
                )
        else:
            hotkey_for_name = Wallet(path=str(wallet_path), name=wallet.name, hotkey=h_name)
        try:
            exists = hotkey_for_name.hotkey_file.exists_on_device() or hotkey_for_name.hotkeypub_file.exists_on_device()
            if exists and not hotkey_for_name.hotkey_file.is_encrypted() and get_hotkey_pub_ss58(hotkey_for_name):
                hotkey_wallets.append(hotkey_for_name)
            elif show_encrypted and exists and hotkey_for_name.hotkey_file.is_encrypted():
                hotkey_wallets.append(WalletLike(str(wallet_path), "<ENCRYPTED>", h_name))
            elif show_nulls:
                hotkey_wallets.append(None)
        except (
            UnicodeDecodeError,
            AttributeError,
            TypeError,
            KeyFileError,
            ValueError,
        ) as e:  # usually an unrelated file like .DS_Store
            print("error occured", e)
            continue

    return hotkey_wallets


def get_public_key_from_keyfile(keyfile_path: Path) -> Optional[str]:
    """
    Extract the SS58 address from a keyfile by reading the public key.
    Bittensor keyfiles store the public key in plaintext (unencrypted).
    """
    try:
        if not keyfile_path.exists():
            return None

        # Read the keyfile JSON
        with open(keyfile_path) as f:
            keyfile_data = json.load(f)

        # The public key is stored in the 'publicKey' or 'public_key' field
        public_key_hex = keyfile_data.get("publicKey") or keyfile_data.get("public_key")

        if not public_key_hex:
            return None

        # Convert hex public key to SS58 address
        from substrateinterface import Keypair

        # Remove '0x' prefix if present
        if public_key_hex.startswith("0x"):
            public_key_hex = public_key_hex[2:]

        # Convert hex to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)

        # Create keypair from public key (ss58_format=42 is for Bittensor)
        keypair = Keypair(public_key=public_key_bytes, ss58_format=42)

        return keypair.ss58_address

    except Exception:
        # Silently return None if we can't read the file
        return None


def get_wallets() -> list[WalletInfo]:
    """
    Scans the wallet directory and retrieves wallet names and addresses
    without decrypting any private keys (only reads public keys).
    """
    from bittensor.utils import KeyFileError
    walletsInfo: list[WalletInfo] = []
    wallet_path = get_wallet_path()
    if not wallet_path.exists():
        Console.warning(f"Bittensor wallet directory not found at: {wallet_path}")
        return []
    wallets = get_coldkey_wallet_from_path(str(wallet_path))

    if not wallets:
        Console.warning(f"No any Bittensor wallets found at: {wallet_path}")
        return wallets

    for wallet in wallets:
        if (
            wallet.coldkeypub_file.exists_on_device()
            and os.path.isfile(wallet.coldkeypub_file.path)
            and not wallet.coldkeypub_file.is_encrypted()
        ):
            coldkeypub_str = wallet.coldkeypub.ss58_address
        else:
            coldkeypub_str = "?"

        hotkeys = get_hotkey_wallets_for_wallet(wallet, show_nulls=True, show_encrypted=True)
        hkeys = []
        for hkey in hotkeys:
            hk_data = {"name": hkey.name, "ss58_address": "?"}
            if hkey:
                try:
                    hkey_ss58 = hkey.get_hotkey().ss58_address
                except KeyFileError:
                    hkey_ss58 = hkey.get_hotkeypub().ss58_address
                except AttributeError:
                    hkey_ss58 = hkey.hotkey.ss58_address
                try:
                    hk_data["name"] = hkey.hotkey_str
                    hk_data["ss58_address"] = hkey_ss58
                except UnicodeDecodeError:
                    pass
            hkeys.append(hk_data)
        # print(hkeys)
        wallet = WalletInfo(
            name=wallet.name,
            path=wallet.path,
            coldkey_address=coldkeypub_str,
            hotkeys=hkeys,
        )
        walletsInfo.append(wallet)
    return walletsInfo


def get_wallet_by_name(name: str, hotkey: str = "default") -> Optional[Wallet]:
    """
    Retrieves and DECRYPTS a specific wallet by its name.
    This function WILL ask for a password and is intended for actions
    that require a decrypted key, like checking balances or making transactions.

    Args:
        name: The name of the wallet (e.g., 'my_coldkey').

    Returns:
        A bittensor wallet object or None if not found.
    """
    try:
        # This is the function that is SUPPOSED to ask for a password.
        wallet = Wallet(name=name, hotkey=hotkey)
        return wallet
    except Exception:
        return None
