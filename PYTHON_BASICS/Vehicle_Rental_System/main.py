"""
main.py
-------
Entry point for the Vehicle Rental System interactive CLI.

Presents a menu-driven interface for managing the vehicle fleet.
All user inputs are validated before reaching the business layer.
No business logic lives here — this module only handles I/O.
"""

from datetime import datetime
from vehicles import Car, Truck, Bike
from rental_system import RentalSystem
from logger import get_logger

logger = get_logger(__name__)
system = RentalSystem()
_CURRENT_YEAR: int = datetime.now().year


# --- Input helpers ---

def prompt_str(label: str) -> str:
    """Repeatedly prompt until the user provides a non-empty string.

    Args:
        label: The prompt text shown to the user.

    Returns:
        A stripped, non-empty string.
    """
    while True:
        value = input(label).strip()
        if value:
            return value
        print("  [!] Input cannot be empty. Please try again.")


def prompt_int(label: str, min_val: int, max_val: int) -> int:
    """Repeatedly prompt until the user provides an integer in [min_val, max_val].

    Args:
        label: The prompt text shown to the user.
        min_val: Minimum accepted value (inclusive).
        max_val: Maximum accepted value (inclusive).

    Returns:
        A validated integer.
    """
    while True:
        raw = input(label).strip()
        try:
            value = int(raw)
            if min_val <= value <= max_val:
                return value
            print(f"  [!] Must be between {min_val} and {max_val}.")
        except ValueError:
            print("  [!] Please enter a whole number.")


def prompt_float(label: str, min_val: float, max_val: float) -> float:
    """Repeatedly prompt until the user provides a float in [min_val, max_val].

    Args:
        label: The prompt text shown to the user.
        min_val: Minimum accepted value (inclusive).
        max_val: Maximum accepted value (inclusive).

    Returns:
        A validated float.
    """
    while True:
        raw = input(label).strip()
        try:
            value = float(raw)
            if min_val <= value <= max_val:
                return value
            print(f"  [!] Must be between {min_val} and {max_val}.")
        except ValueError:
            print("  [!] Please enter a valid number.")


# --- Menu actions ---

def add_vehicle() -> None:
    """Collect vehicle details interactively and register the vehicle in the fleet."""
    print("\n  Vehicle type:  1) Car   2) Truck   3) Bike")
    vehicle_type = prompt_str("  Choose (1/2/3): ")
    if vehicle_type not in ("1", "2", "3"):
        print("  [!] Invalid vehicle type selection.")
        logger.warning("Invalid vehicle type entered: %s", vehicle_type)
        return

    vehicle_id = prompt_str("  Vehicle ID      : ")
    make       = prompt_str("  Make            : ")
    model      = prompt_str("  Model           : ")
    year       = prompt_int(f"  Year (1886-{_CURRENT_YEAR + 1}): ", 1886, _CURRENT_YEAR + 1)
    base_rate  = prompt_float("  Base rate $/day : ", 1.0, 9999.0)

    try:
        if vehicle_type == "1":
            num_passengers = prompt_int("  Passengers (1-15): ", 1, 15)
            system.add_vehicle(Car(vehicle_id, make, model, year, base_rate, num_passengers))
        elif vehicle_type == "2":
            payload_tons = prompt_float("  Payload tons (0.1-50): ", 0.1, 50.0)
            system.add_vehicle(Truck(vehicle_id, make, model, year, base_rate, payload_tons))
        else:
            engine_cc = prompt_int("  Engine cc (50-2500): ", 50, 2500)
            system.add_vehicle(Bike(vehicle_id, make, model, year, base_rate, engine_cc))
        print("  [+] Vehicle added successfully.")
    except ValueError as exc:
        print(f"  [!] {exc}")
        logger.error("Failed to add vehicle: %s", exc)


def rent_vehicle() -> None:
    """Prompt for a vehicle ID and rental duration, then process the rental."""
    vehicle_id = prompt_str("\n  Vehicle ID to rent : ")
    days       = prompt_int("  Number of days (1-365): ", 1, 365)
    try:
        system.rent_vehicle(vehicle_id, days)
    except (ValueError, RuntimeError) as exc:
        print(f"  [!] {exc}")
        logger.error("Rent failed: %s", exc)


def return_vehicle() -> None:
    """Prompt for a rental ID and process the vehicle return."""
    rental_id = prompt_str("\n  Rental ID to return (e.g. R0001): ")
    try:
        system.return_vehicle(rental_id)
    except ValueError as exc:
        print(f"  [!] {exc}")
        logger.error("Return failed: %s", exc)


def update_base_rate() -> None:
    """Prompt for a vehicle ID and new base rate, then apply the update."""
    vehicle_id = prompt_str("\n  Vehicle ID to update: ")
    vehicle = system.get_vehicle(vehicle_id)
    if vehicle is None:
        print(f"  [!] No vehicle with ID '{vehicle_id.upper()}' found.")
        logger.warning("Rate update attempted for unknown vehicle: %s", vehicle_id)
        return
    new_rate = prompt_float("  New base rate $/day (1-9999): ", 1.0, 9999.0)
    try:
        vehicle.base_rate = new_rate
        print(f"  [+] Base rate updated to ${vehicle.base_rate:.2f}/day.")
    except ValueError as exc:
        print(f"  [!] {exc}")
        logger.error("Rate update failed for %s: %s", vehicle_id, exc)


# --- Main loop ---

MENU = """
================================
    Vehicle Rental System
================================
  1) Add vehicle
  2) Show fleet availability
  3) Rent a vehicle
  4) Return a vehicle
  5) View active rentals
  6) View rental history
  7) Update vehicle base rate
  8) Exit
================================"""

_ACTIONS = {
    "1": add_vehicle,
    "2": system.display_availability,
    "3": rent_vehicle,
    "4": return_vehicle,
    "5": system.display_active_rentals,
    "6": system.display_rental_history,
    "7": update_base_rate,
}


def main() -> None:
    """Run the interactive CLI loop until the user chooses to exit."""
    logger.info("Vehicle Rental System started.")
    while True:
        print(MENU)
        choice = input("  Select option: ").strip()
        if choice == "8":
            print("\n  Goodbye!\n")
            logger.info("Vehicle Rental System exited by user.")
            break
        action = _ACTIONS.get(choice)
        if action:
            action()
        else:
            print("  [!] Invalid option - please choose 1 to 8.")
            logger.warning("Invalid menu option entered: %s", choice)


if __name__ == "__main__":
    main()
