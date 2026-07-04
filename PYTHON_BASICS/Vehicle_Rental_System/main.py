"""
main.py
-------
Entry point for the Vehicle Rental System CLI.

Presents an interactive menu that lets users add vehicles, view fleet
availability, rent/return vehicles, and update base rates.  All user
inputs are validated before being passed to the business layer.
"""

from datetime import datetime
from vehicles import Car, Truck, Bike
from rental_system import RentalSystem
from logger import get_logger

logger = get_logger(__name__)
system = RentalSystem()
_CURRENT_YEAR = datetime.now().year

# ------------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------------

def _prompt_str(prompt: str) -> str:
    """Prompt until the user enters a non-empty string.

    Args:
        prompt: The message displayed to the user.

    Returns:
        A stripped, non-empty string.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  Input cannot be empty. Please try again.")


def _prompt_int(prompt: str, min_val: int, max_val: int) -> int:
    """Prompt until the user enters an integer within [min_val, max_val].

    Args:
        prompt: The message displayed to the user.
        min_val: Minimum accepted value (inclusive).
        max_val: Maximum accepted value (inclusive).

    Returns:
        A validated integer.
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if min_val <= value <= max_val:
                return value
            print(f"  Must be between {min_val} and {max_val}. Please try again.")
        except ValueError:
            print("  Invalid input — please enter a whole number.")


def _prompt_float(prompt: str, min_val: float, max_val: float) -> float:
    """Prompt until the user enters a float within [min_val, max_val].

    Args:
        prompt: The message displayed to the user.
        min_val: Minimum accepted value (inclusive).
        max_val: Maximum accepted value (inclusive).

    Returns:
        A validated float.
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if min_val <= value <= max_val:
                return value
            print(f"  Must be between {min_val} and {max_val}. Please try again.")
        except ValueError:
            print("  Invalid input — please enter a number.")


# ------------------------------------------------------------------
# Menu actions
# ------------------------------------------------------------------

def add_vehicle():
    """Collect vehicle details from the user and register it in the fleet."""
    print("\nVehicle type: 1) Car  2) Truck  3) Bike")
    v_type = _prompt_str("Choose (1/2/3): ")
    if v_type not in ("1", "2", "3"):
        print("  Invalid vehicle type.")
        logger.warning("Invalid vehicle type entered: %s", v_type)
        return

    vid  = _prompt_str("Vehicle ID: ")
    make = _prompt_str("Make: ")
    model = _prompt_str("Model: ")
    year = _prompt_int(f"Year (1886–{_CURRENT_YEAR + 1}): ", 1886, _CURRENT_YEAR + 1)
    rate = _prompt_float("Base rate ($/day, 1–9999): ", 1.0, 9999.0)

    try:
        if v_type == "1":
            passengers = _prompt_int("Number of passengers (1–15): ", 1, 15)
            system.add_vehicle(Car(vid, make, model, year, rate, passengers))
        elif v_type == "2":
            payload = _prompt_float("Payload capacity in tons (0.1–50): ", 0.1, 50.0)
            system.add_vehicle(Truck(vid, make, model, year, rate, payload))
        else:
            cc = _prompt_int("Engine size in cc (50–2500): ", 50, 2500)
            system.add_vehicle(Bike(vid, make, model, year, rate, cc))
        print("  Vehicle added successfully.")
    except ValueError as e:
        print(f"  Error: {e}")
        logger.error("Failed to add vehicle: %s", e)


def rent_vehicle():
    """Prompt for a vehicle ID and rental duration, then process the rental."""
    vid  = _prompt_str("\nVehicle ID to rent: ")
    days = _prompt_int("Number of days (1–365): ", 1, 365)
    try:
        system.rent_vehicle(vid, days)
    except (ValueError, RuntimeError) as e:
        print(f"  Error: {e}")
        logger.error("Rent failed: %s", e)


def return_vehicle():
    """Prompt for a rental ID and process the vehicle return."""
    rid = _prompt_str("\nRental ID to return (e.g. R0001): ")
    try:
        system.return_vehicle(rid)
    except ValueError as e:
        print(f"  Error: {e}")
        logger.error("Return failed: %s", e)


def update_rate():
    """Prompt for a vehicle ID and new base rate, then apply the update."""
    vid = _prompt_str("\nVehicle ID to update: ")
    vehicle = system._fleet.get(vid)
    if vehicle is None:
        print(f"  No vehicle with ID '{vid}' found.")
        logger.warning("Rate update attempted for unknown vehicle: %s", vid)
        return
    new_rate = _prompt_float("New base rate ($/day, 1–9999): ", 1.0, 9999.0)
    try:
        vehicle.base_rate = new_rate
        print(f"  Base rate updated to ${vehicle.base_rate:.2f}/day.")
    except ValueError as e:
        print(f"  Error: {e}")
        logger.error("Rate update failed for %s: %s", vid, e)


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

MENU = """
=== Vehicle Rental System ===
1) Add vehicle
2) Show availability
3) Rent a vehicle
4) Return a vehicle
5) Update vehicle base rate
6) Exit
"""


def main():
    """Run the interactive CLI loop."""
    logger.info("Vehicle Rental System started.")
    while True:
        print(MENU)
        choice = input("Select option: ").strip()
        if choice == "1":
            add_vehicle()
        elif choice == "2":
            system.display_availability()
        elif choice == "3":
            rent_vehicle()
        elif choice == "4":
            return_vehicle()
        elif choice == "5":
            update_rate()
        elif choice == "6":
            print("Goodbye!")
            logger.info("Vehicle Rental System exited by user.")
            break
        else:
            print("  Invalid option — please choose 1 to 6.")
            logger.warning("Invalid menu option entered: %s", choice)


if __name__ == "__main__":
    main()
