from vehicles import Car, Truck, Bike
from rental_system import RentalSystem

system = RentalSystem()


def add_vehicle():
    print("\nVehicle type: 1) Car  2) Truck  3) Bike")
    choice = input("Choose: ").strip()
    vid = input("Vehicle ID: ").strip()
    make = input("Make: ").strip()
    model = input("Model: ").strip()
    year = int(input("Year: ").strip())
    rate = float(input("Base rate ($/day): ").strip())

    if choice == "1":
        passengers = int(input("Number of passengers: ").strip())
        system.add_vehicle(Car(vid, make, model, year, rate, passengers))
    elif choice == "2":
        payload = float(input("Payload capacity (tons): ").strip())
        system.add_vehicle(Truck(vid, make, model, year, rate, payload))
    elif choice == "3":
        cc = int(input("Engine size (cc): ").strip())
        system.add_vehicle(Bike(vid, make, model, year, rate, cc))
    else:
        print("Invalid choice.")
        return
    print("Vehicle added successfully.")


def rent_vehicle():
    vid = input("\nEnter Vehicle ID to rent: ").strip()
    days = int(input("Number of days: ").strip())
    try:
        system.rent_vehicle(vid, days)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")


def return_vehicle():
    rid = input("\nEnter Rental ID to return: ").strip()
    try:
        system.return_vehicle(rid)
    except ValueError as e:
        print(f"Error: {e}")


def update_rate():
    vid = input("\nEnter Vehicle ID to update rate: ").strip()
    vehicle = system._fleet.get(vid)
    if vehicle is None:
        print(f"No vehicle with ID '{vid}' found.")
        return
    try:
        new_rate = float(input("New base rate ($/day): ").strip())
        vehicle.base_rate = new_rate
        print(f"Base rate updated to ${vehicle.base_rate:.2f}/day.")
    except ValueError as e:
        print(f"Error: {e}")


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
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
