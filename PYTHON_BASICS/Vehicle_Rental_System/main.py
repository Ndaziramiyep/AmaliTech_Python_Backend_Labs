from vehicles import Car, Truck, Bike
from rental_system import RentalSystem


def main():
    system = RentalSystem()

    # Populate fleet
    system.add_vehicle(Car("C001", "Toyota", "Camry", 2022, base_rate=40.0, num_passengers=5))
    system.add_vehicle(Car("C002", "Honda", "Civic", 2021, base_rate=35.0, num_passengers=4))
    system.add_vehicle(Truck("T001", "Ford", "F-150", 2020, base_rate=70.0, payload_tons=1.5))
    system.add_vehicle(Truck("T002", "Chevy", "Silverado", 2023, base_rate=80.0, payload_tons=2.0))
    system.add_vehicle(Bike("B001", "Yamaha", "MT-07", 2022, base_rate=25.0, engine_cc=689))
    system.add_vehicle(Bike("B002", "Honda", "CBR300R", 2021, base_rate=20.0, engine_cc=286))

    system.display_availability()

    # Rent some vehicles
    r1 = system.rent_vehicle("C001", days=3)
    r2 = system.rent_vehicle("T001", days=5)
    r3 = system.rent_vehicle("B001", days=2)

    system.display_availability()

    # Return a vehicle
    system.return_vehicle(r1)

    # Demonstrate error handling
    try:
        system.rent_vehicle("C001", days=1)  # just returned, should succeed
        system.rent_vehicle("T001", days=1)  # still rented, should fail
    except RuntimeError as e:
        print(f"Error: {e}")

    # Update base rate via property
    fleet_car = system._fleet["C002"]
    fleet_car.base_rate = 38.0
    print(f"\nUpdated base rate for C002: ${fleet_car.base_rate:.2f}/day")

    system.display_availability()

    # Return remaining rentals
    system.return_vehicle(r2)
    system.return_vehicle(r3)


if __name__ == "__main__":
    main()
