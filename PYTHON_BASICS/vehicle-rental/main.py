"""Entry point for the Vehicle Rental System CLI."""

from rental_system import RentalSystem
from vehicle.bike import Bike
from vehicle.car import Car
from vehicle.truck import Truck


def _add_vehicle_prompt(system: RentalSystem) -> None:
    """Prompt the user to create and add a new vehicle to the fleet."""
    print("\n  Choose vehicle type:")
    print("  1. Car")
    print("  2. Bike")
    print("  3. Truck")
    vtype = input("  Enter type: ").strip()

    vid = input("  Enter Vehicle ID  : ").strip()
    if not vid:
        print("  Vehicle ID cannot be empty. Vehicle not added.")
        return
    brand = input("  Enter Brand       : ").strip()
    if not brand:
        print("  Brand cannot be empty. Vehicle not added.")
        return

    try:
        base_price = float(input("  Enter Rate/Day ($): ").strip())
        if base_price <= 0:
            raise ValueError
    except ValueError:
        print("  Rate must be a positive number. Vehicle not added.")
        return

    vehicle_map = {"1": Car, "2": Bike, "3": Truck}
    cls = vehicle_map.get(vtype)
    if cls is None:
        print("  Invalid vehicle type.")
        return

    system.add_vehicle(cls(vid, brand, base_price))
    print(f"  '{vid}' added successfully.")


def main() -> None:
    """Run the Vehicle Rental System interactive CLI."""
    system = RentalSystem()

    # Seed sample vehicles so the system is usable immediately
    system.add_vehicle(Car("C001", "Toyota", 50.0))
    system.add_vehicle(Car("C002", "Honda", 45.0))
    system.add_vehicle(Bike("B001", "Yamaha", 20.0))
    system.add_vehicle(Truck("T001", "Ford", 100.0))
    menu = (
        "\n--- Vehicle Rental System ---\n"
        "1. Show all vehicles\n"
        "2. Show available vehicles\n"
        "3. Show rented vehicles\n"
        "4. Rent a vehicle\n"
        "5. Return a vehicle\n"
        "6. Calculate rental cost\n"
        "7. Add a new vehicle\n"
        "8. Exit"
    )

    actions = {
        "1": lambda: system.show_all(),
        "2": lambda: system.show_available(),
        "3": lambda: system.show_rented(),
    }

    while True:
        print(menu)
        choice = input("Enter choice: ").strip()

        if choice in actions:
            actions[choice]()

        elif choice == "4":
            vid = input("  Enter Vehicle ID to rent: ").strip()
            if not vid:
                print("  Vehicle ID cannot be empty.")
                continue
            system.rent_vehicle(vid)

        elif choice == "5":
            vid = input("  Enter Vehicle ID to return: ").strip()
            if not vid:
                print("  Vehicle ID cannot be empty.")
                continue
            system.return_vehicle(vid)

        elif choice == "6":
            vid = input("  Enter Vehicle ID: ").strip()
            if not vid:
                print("  Vehicle ID cannot be empty.")
                continue
            try:
                days = int(input("  Enter number of days: ").strip())
                if days < 1:
                    raise ValueError
            except ValueError:
                print("  Days must be a positive whole number.")
                continue
            system.calculate_cost(vid, days)

        elif choice == "7":
            _add_vehicle_prompt(system)

        elif choice == "8":
            print("Goodbye!")
            break

        else:
            print("  Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
