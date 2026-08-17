from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Building, Unit, Vendor, BuildingType, IssueCategory

def seed_data():
    create_db_and_tables()
    with Session(engine) as session:
        # Check if already seeded
        if session.exec(select(Building)).first():
            print("Database already seeded.")
            return

        print("Seeding database...")
        # Vendors
        vendors = [
            Vendor(name="Plumbing Pros", category=IssueCategory.PLUMBING, email="contact@plumbingpros.com", phone="555-0100"),
            Vendor(name="Sparky Electrical", category=IssueCategory.ELECTRICAL, email="hello@sparky.com", phone="555-0200"),
            Vendor(name="Cooling & Lifts", category=IssueCategory.ELEVATOR_HVAC, email="support@coolinglifts.com", phone="555-0300"),
            Vendor(name="Secure Access Co", category=IssueCategory.ACCESS_CONTROL, email="security@secureaccess.com", phone="555-0400"),
        ]
        session.add_all(vendors)

        # Buildings
        b1 = Building(name="Sunset Apartments Block B", type=BuildingType.RESIDENTIAL, address="123 Sunset Blvd")
        b2 = Building(name="Downtown Towers", type=BuildingType.COMMERCIAL, address="456 Main St")
        b3 = Building(name="Ministry Annex", type=BuildingType.GOVERNMENT, address="Rua da Prata")
        
        session.add_all([b1, b2, b3])
        session.commit() # Commit to get IDs

        # Units
        units = [
            Unit(building_id=b1.id, unit_identifier="Apt 1A"),
            Unit(building_id=b1.id, unit_identifier="Apt 1B"),
            Unit(building_id=b1.id, unit_identifier="Apt 2A"),
            Unit(building_id=b1.id, unit_identifier="Apt 3C"),
            Unit(building_id=b1.id, unit_identifier="5th floor"),
            Unit(building_id=b1.id, unit_identifier="Garage Level -1"),
            Unit(building_id=b1.id, unit_identifier="Garage Level -2"),
            Unit(building_id=b2.id, unit_identifier="Floor 1"),
            Unit(building_id=b2.id, unit_identifier="Floor 2"),
            Unit(building_id=b3.id, unit_identifier="Lobby"),
            Unit(building_id=b3.id, unit_identifier="Front Door"),
        ]
        session.add_all(units)
        session.commit()
        print("Database seeding completed.")

if __name__ == "__main__":
    seed_data()
