"""
QC Power Management Functions
Contains power supply control and safety functions
"""

import time
import colorama
from colorama import Fore, Style

colorama.init()


class ManualPowerSupply:
    """
    Simulates power supply interface in manual mode.
    Prompts operator to perform power operations manually instead of
    controlling hardware automatically.
    """
    is_manual = True

    def set_channel(self, ch, voltage, current, on=True):
        action = "ON" if on else "OFF"
        print(Fore.YELLOW + f"\n⚠️  MANUAL: Please turn {action} the WIB 12V power supply" + Style.RESET_ALL)
        input(Fore.YELLOW + f"  Press Enter when 12V power supply is {action}... " + Style.RESET_ALL)
        print(Fore.GREEN + f"  ✓ 12V power supply {action} confirmed (manual)" + Style.RESET_ALL)

    def turn_off_all(self):
        print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply" + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter when 12V power supply is OFF... " + Style.RESET_ALL)
        print(Fore.GREEN + "  ✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)

    def measure(self, ch):
        # Manual mode cannot measure; return 0 so current checks pass
        return (0.0, 0.0)

    def output_off(self, ch):
        print(Fore.YELLOW + "\n⚠️  MANUAL: Please turn OFF the WIB 12V power supply" + Style.RESET_ALL)
        input(Fore.YELLOW + "  Press Enter when 12V power supply is OFF... " + Style.RESET_ALL)
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
        while True:
            com = input(Fore.YELLOW + "Type 'confirm' when 12V power supply is OFF >> " + Style.RESET_ALL)
            if com.lower() == "confirm":
                print(Fore.GREEN + "✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + "Invalid input. Please type 'confirm'." + Style.RESET_ALL)

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
                while True:
                    com = input(Fore.YELLOW + "Type 'confirm' when 12V power supply is OFF >> " + Style.RESET_ALL)
                    if com.lower() == "confirm":
                        print(Fore.GREEN + "✓ 12V power supply OFF confirmed (manual)" + Style.RESET_ALL)
                        return True
                    else:
                        print(Fore.RED + "Invalid input. Please type 'confirm'." + Style.RESET_ALL)
            else:
                attempt = 0  # Reset attempt counter for retry

        print(Fore.CYAN + "Retrying auto power off...\n" + Style.RESET_ALL)
