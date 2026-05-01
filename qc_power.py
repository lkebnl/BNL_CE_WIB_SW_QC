"""
QC Power Management Functions
Contains power supply control and safety functions
"""

import time
import colorama
from colorama import Fore, Style
import GUI.send_email as send_email

colorama.init()


class ManualPowerSupply:
    """
    Simulates power supply interface in manual mode.
    Prompts operator to perform power operations manually instead of
    controlling hardware automatically.
    """
    is_manual = True

    def __init__(self, email_info=None):
        self.email_info = email_info  # dict with keys: sender, password, receiver

    def set_channel(self, ch, voltage, current, on=True):
        action = "ON" if on else "OFF"
        print(Fore.YELLOW + f"\n⚠️  MANUAL: Please turn {action} the WIB 12V power supply" + Style.RESET_ALL)
        if on:
            if self.email_info:
                try:
                    send_email.send_email(
                        self.email_info['sender'], self.email_info['password'],
                        self.email_info['receiver'],
                        "ACTION REQUIRED: Please turn ON WIB 12V power supply",
                        "Please turn ON the WIB 12V power supply now, then confirm in the terminal."
                    )
                    print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
                except Exception as e:
                    print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
            while True:
                com = input(Fore.YELLOW + "  Type 'WIB12v on' to confirm power is ON >> " + Style.RESET_ALL)
                if com.strip().lower() == 'wib12v on':
                    break
                print(Fore.RED + "  Invalid input. Please type 'WIB12v on'." + Style.RESET_ALL)
        else:
            if self.email_info:
                try:
                    send_email.send_email(
                        self.email_info['sender'], self.email_info['password'],
                        self.email_info['receiver'],
                        "ACTION REQUIRED: Please turn OFF WIB 12V power supply",
                        "Please turn OFF the WIB 12V power supply now, then confirm in the terminal."
                    )
                    print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
                except Exception as e:
                    print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
            while True:
                com = input(Fore.YELLOW + "  Type 'WIB12v off' to confirm power is OFF >> " + Style.RESET_ALL)
                if com.strip().lower() == 'wib12v off':
                    break
                print(Fore.RED + "  Invalid input. Please type 'WIB12v off'." + Style.RESET_ALL)
        print(Fore.GREEN + f"  ✓ 12V power supply {action} confirmed (manual)" + Style.RESET_ALL)

    def turn_off_all(self):
        print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply" + Style.RESET_ALL)
        if self.email_info:
            try:
                send_email.send_email(
                    self.email_info['sender'], self.email_info['password'],
                    self.email_info['receiver'],
                    "ACTION REQUIRED: Please turn OFF WIB 12V power supply",
                    "Please turn OFF the WIB 12V power supply now, then confirm in the terminal."
                )
                print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
        while True:
            com = input(Fore.YELLOW + "  Type 'WIB12v off' to confirm power is OFF >> " + Style.RESET_ALL)
            if com.strip().lower() == 'wib12v off':
                break
            print(Fore.RED + "  Invalid input. Please type 'WIB12v off'." + Style.RESET_ALL)
        print(Fore.GREEN + "  ✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)

    def measure(self, ch):
        # Manual mode cannot measure; return 0 so current checks pass
        return (0.0, 0.0)

    def output_off(self, ch):
        print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply" + Style.RESET_ALL)
        if self.email_info:
            try:
                send_email.send_email(
                    self.email_info['sender'], self.email_info['password'],
                    self.email_info['receiver'],
                    "ACTION REQUIRED: Please turn OFF WIB 12V power supply",
                    "Please turn OFF the WIB 12V power supply now, then confirm in the terminal."
                )
                print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
        while True:
            com = input(Fore.YELLOW + "  Type 'WIB12v off' to confirm power is OFF >> " + Style.RESET_ALL)
            if com.strip().lower() == 'wib12v off':
                break
            print(Fore.RED + "  Invalid input. Please type 'WIB12v off'." + Style.RESET_ALL)
        print(Fore.GREEN + "  ✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)

    def close(self):
        pass


def safe_power_off(psu, current_threshold=0.2, max_attempts=5):
    """
    Power off WIB. In manual mode prompts operator; in auto mode attempts
    up to max_attempts times before falling back to manual confirmation.
    """
    if getattr(psu, 'is_manual', False):
        print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply and check the current is zero" + Style.RESET_ALL)
        _email_info = getattr(psu, 'email_info', None)
        if _email_info:
            try:
                send_email.send_email(
                    _email_info['sender'], _email_info['password'],
                    _email_info['receiver'],
                    "ACTION REQUIRED: Please turn OFF WIB 12V power supply",
                    "Please turn OFF the WIB 12V power supply now, then confirm in the terminal."
                )
                print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
        while True:
            com = input(Fore.YELLOW + "  Type 'WIB12v off' to confirm power is OFF >> " + Style.RESET_ALL)
            if com.strip().lower() == 'wib12v off':
                print(Fore.GREEN + "✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + "  Invalid input. Please type 'WIB12v off'." + Style.RESET_ALL)

    attempt = 0
    while True:
        time.sleep(1)
        # Measure current on both channels
        total_i = 0
        for ch in (1, 2):
            v, i = psu.measure(ch)
            print(f"  CH{ch}: {v:.3f} V, {i:.3f} A")
            total_i += i
        print(Fore.CYAN + f"  Total current: {total_i:.3f} A" + Style.RESET_ALL)

        # Attempt power off
        psu.turn_off_all()

        # Success
        if total_i < current_threshold:
            print(Fore.GREEN + "✓ Power OFF successful." + Style.RESET_ALL)
            return True

        # Failed → auto retry
        attempt += 1
        print(
            Fore.YELLOW + f"⚠️  Power off attempt {attempt}/{max_attempts} failed (current too high)." + Style.RESET_ALL)

        # Max attempts reached → offer manual mode switch or manual intervention
        if attempt >= max_attempts:
            print(Fore.RED + "\n" + "=" * 60)
            print("⚠️  WARNING: AUTO POWER-OFF FAILED")
            print("=" * 60 + "\n" + Style.RESET_ALL)
            print(Fore.YELLOW + "Options:" + Style.RESET_ALL)
            print("  M - Switch to manual mode (operator controls power supply)")
            print("  R - Retry auto power off")
            choice = input(Fore.YELLOW + "Enter choice (M/R) >> " + Style.RESET_ALL).strip().upper()
            if choice == 'M':
                print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply and check the current is zero" + Style.RESET_ALL)
                _email_info = getattr(psu, 'email_info', None)
                if _email_info:
                    try:
                        send_email.send_email(
                            _email_info['sender'], _email_info['password'],
                            _email_info['receiver'],
                            "ACTION REQUIRED: Please turn OFF WIB 12V power supply",
                            "Please turn OFF the WIB 12V power supply now, then confirm in the terminal."
                        )
                        print(Fore.CYAN + "  ✉ Email notification sent to tester." + Style.RESET_ALL)
                    except Exception as e:
                        print(Fore.RED + f"  ✗ Failed to send email: {e}" + Style.RESET_ALL)
                while True:
                    com = input(Fore.YELLOW + "  Type 'WIB12v off' to confirm power is OFF >> " + Style.RESET_ALL)
                    if com.strip().lower() == 'wib12v off':
                        print(Fore.GREEN + "✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)
                        return True
                    else:
                        print(Fore.RED + "  Invalid input. Please type 'WIB12v off'." + Style.RESET_ALL)
            else:
                attempt = 0  # Reset attempt counter for retry

        print(Fore.CYAN + "Retrying auto power off...\n" + Style.RESET_ALL)
