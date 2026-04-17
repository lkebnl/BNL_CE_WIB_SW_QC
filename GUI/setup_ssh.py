# -*- coding: utf-8 -*-
"""WIB SSH setup helper for Windows.

This version is intentionally conservative:
- It does NOT overwrite an existing local key pair.
- It adds the WIB host key to the user's known_hosts file.
- It appends the local public key to WIB's authorized_keys only if it is not already present.
- Tkinter UI updates are scheduled on the main thread.

Dependencies:
- Windows OpenSSH tools available on PATH: ssh-keygen, ssh-keyscan
- Python package: paramiko
"""

from __future__ import annotations

import os
import platform
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Tuple

WIB_IP = "192.168.121.123"
WIB_USER = "root"
WIB_HOST = f"{WIB_USER}@{WIB_IP}"

SSH_DIR = Path.home() / ".ssh"
KEY_PATH = SSH_DIR / "id_rsa"
PUB_PATH = SSH_DIR / "id_rsa.pub"
KNOWN_HOSTS = SSH_DIR / "known_hosts"


def run_cmd(args: list[str], timeout: int = 30, input_text: str | None = None) -> Tuple[int, str]:
    """Run a subprocess and return (returncode, output)."""
    try:
        r = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "Timeout"
    except FileNotFoundError as e:
        return -1, str(e)
    except Exception as e:
        return -1, str(e)


def ensure_local_keypair() -> str:
    """Create an RSA keypair only if it does not already exist."""
    SSH_DIR.mkdir(parents=True, exist_ok=True)

    if KEY_PATH.exists() and PUB_PATH.exists():
        return "Local key pair already exists; reusing it."

    # If one file exists but the other doesn't, clean up the broken pair.
    for p in (KEY_PATH, PUB_PATH):
        if p.exists():
            p.unlink()

    rc, out = run_cmd([
        "ssh-keygen",
        "-t", "rsa",
        "-b", "2048",
        "-N", "",
        "-f", str(KEY_PATH),
    ], timeout=60)
    if rc != 0:
        raise RuntimeError(f"ssh-keygen failed: {out.strip()}")

    return f"Generated new key pair at {KEY_PATH} and {PUB_PATH}."


def ensure_known_host(ip: str) -> str:
    """Fetch WIB host key with ssh-keyscan and add it to known_hosts.

    This is TOFU-based: it trusts the host key returned by ssh-keyscan.
    For a stricter workflow, compare the fingerprint against a known-good value.
    """
    rc, out = run_cmd(["ssh-keyscan", "-H", ip], timeout=20)
    if rc != 0 or not out.strip():
        raise RuntimeError(f"ssh-keyscan failed for {ip}: {out.strip()}")

    SSH_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    if KNOWN_HOSTS.exists():
        existing = KNOWN_HOSTS.read_text(encoding="utf-8", errors="ignore").splitlines(True)

    scan_lines = out.splitlines(True)

    # Remove stale entries for this IP while keeping other hosts intact.
    filtered = []
    for line in existing:
        if line.startswith(f"|"):
            # Hashed entries cannot be matched by plain IP reliably; keep them.
            filtered.append(line)
        elif ip in line:
            continue
        else:
            filtered.append(line)

    # Avoid duplicating the exact same host key lines.
    for line in scan_lines:
        if line not in filtered:
            filtered.append(line)

    KNOWN_HOSTS.write_text("".join(filtered), encoding="utf-8")
    return f"Saved host key to {KNOWN_HOSTS}."


def read_public_key() -> str:
    if not PUB_PATH.exists():
        raise RuntimeError(f"Public key not found: {PUB_PATH}")
    return PUB_PATH.read_text(encoding="utf-8").strip()


def set_remote_authorized_key(password: str) -> str:
    """Overwrite /root/.ssh/authorized_keys on WIB with the local public key."""
    try:
        import paramiko
    except ImportError as e:
        raise RuntimeError(
            "paramiko is not installed. Run: pip install paramiko"
        ) from e

    pub_key = read_public_key()

    client = paramiko.SSHClient()
    client.load_host_keys(str(KNOWN_HOSTS))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        WIB_IP,
        username=WIB_USER,
        password=password,
        timeout=15,
        banner_timeout=15,
        auth_timeout=15,
        look_for_keys=False,
        allow_agent=False,
    )

    try:
        # Create ~/.ssh with safe permissions.
        _stdin, stdout, stderr = client.exec_command(
            "mkdir -p /root/.ssh && chmod 700 /root/.ssh"
        )
        stdout.channel.recv_exit_status()

        remote_path = "/root/.ssh/authorized_keys"
        sftp = client.open_sftp()
        try:
            with sftp.open(remote_path, "w") as f:
                f.write(pub_key + "\n")
            sftp.chmod(remote_path, 0o600)
        finally:
            sftp.close()

        # Verify content really matches exactly what we wrote.
        _stdin, stdout, stderr = client.exec_command(f"cat {remote_path}")
        verify = stdout.read().decode("utf-8", errors="ignore").strip()
        if verify != pub_key:
            raise RuntimeError("authorized_keys verification failed after upload.")

        return "Overwrote /root/.ssh/authorized_keys with the local public key."
    finally:
        client.close()


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("WIB SSH Setup")
        self.root.resizable(False, False)

        frm = ttk.Frame(self.root, padding=12)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text=f"Target: {WIB_HOST}", font=("Courier", 10)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(frm, text="WIB root password:").grid(row=1, column=0, sticky="e")
        self.pwd_var = tk.StringVar()
        self.pwd_entry = ttk.Entry(frm, textvariable=self.pwd_var, show="*", width=28)
        self.pwd_entry.grid(row=1, column=1, sticky="w", padx=(6, 0))
        self.pwd_entry.focus()

        self.text = tk.Text(
            frm,
            width=70,
            height=16,
            state="disabled",
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
        )
        self.text.grid(row=2, column=0, columnspan=2, pady=8)

        self.btn = ttk.Button(frm, text="Setup SSH", command=self.on_click)
        self.btn.grid(row=3, column=0, columnspan=2)

        self.root.bind("<Return>", lambda _e: self.on_click())

    def log(self, msg: str) -> None:
        def _append() -> None:
            self.text.configure(state="normal")
            self.text.insert(tk.END, msg + "\n")
            self.text.see(tk.END)
            self.text.configure(state="disabled")

        self.root.after(0, _append)

    def set_busy(self, busy: bool) -> None:
        def _apply() -> None:
            self.btn.configure(state="disabled" if busy else "normal")
            self.pwd_entry.configure(state="disabled" if busy else "normal")

        self.root.after(0, _apply)

    def on_click(self) -> None:
        password = self.pwd_var.get().strip()
        if not password:
            messagebox.showwarning("Missing password", "Please enter the WIB root password.")
            return

        self.set_busy(True)
        threading.Thread(target=self.worker, args=(password,), daemon=True).start()

    def worker(self, password: str) -> None:
        try:
            self.log("[1/4] Checking local SSH directory...")
            SSH_DIR.mkdir(parents=True, exist_ok=True)

            self.log("[2/4] Ensuring local key pair...")
            msg = ensure_local_keypair()
            self.log("  " + msg)

            self.log(f"[3/4] Adding host key for {WIB_IP}...")
            msg = ensure_known_host(WIB_IP)
            self.log("  " + msg)

            self.log(f"[4/4] Connecting to {WIB_HOST} and overwriting authorized_keys...")
            msg = set_remote_authorized_key(password)
            self.log("  " + msg)

            self.log("\nDone. The WIB authorized_keys file now contains only this PC public key.")
            self.log("Use your password this one time for setup; later SSH logins should use the private key automatically.")
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                "SSH setup complete.\n\n"
                "Local key pair was reused or created,\n"
                "host key was added to known_hosts,\n"
                "and WIB authorized_keys was overwritten with this PC public key.",
            ))
        except Exception as e:
            self.log(f"\nERROR: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.set_busy(False)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    if platform.system().lower() != "windows":
        print("Warning: this script was designed for Windows.")
    App().run()


if __name__ == "__main__":
    main()
