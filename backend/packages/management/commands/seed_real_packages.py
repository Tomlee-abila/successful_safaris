from django.core.management.base import BaseCommand
from destinations.models import Destination, SafariLocation
from packages.models import SafariPackage, PackageItinerary


class Command(BaseCommand):
    help = (
        "Adds the real, client-supplied safari packages (from actual costing sheets, "
        "not demo/fake data). Idempotent: safe to re-run, matches on package_code, "
        "never deletes or touches the random demo packages seeded by seed_business."
    )

    def handle(self, *args, **kwargs):
        kenya, _ = Destination.objects.get_or_create(
            name="Kenya",
            defaults={
                "description": "The jewel of East Africa, home to the Masai Mara and diverse wildlife.",
                "best_travel_season": "June to October (Dry Season)",
                "visa_information": "Visa required for most nationalities, e-visas available.",
                "health_requirements": "Yellow Fever certificate required if traveling from endemic zones.",
                "featured_wildlife": "The Big Five",
            },
        )

        def location(name, activities, wildlife):
            loc, _ = SafariLocation.objects.get_or_create(
                destination=kenya,
                name=name,
                defaults={
                    "description": f"{name}, Kenya.",
                    "activities": activities,
                    "wildlife": wildlife,
                },
            )
            return loc

        watamu = location(
            "Watamu",
            "Snorkeling, Coral Garden Walk, Birdwalking, Herping",
            "Coastal birdlife, marine life, reptiles",
        )
        nairobi = location(
            "Nairobi",
            "City tour, Museum visit, Snake Park",
            "N/A",
        )
        masai_mara = location(
            "Masai Mara National Reserve",
            "Game Drives, Masai Village Tour",
            "Big Five, wildebeest migration",
        )
        lake_nakuru = location(
            "Lake Nakuru National Park",
            "Game Drives",
            "White and black rhino, Grey Crowned Crane",
        )
        naivasha = location(
            "Naivasha",
            "Crescent Island walking safari, Hell's Gate geothermal spa, boat rides",
            "Zebras, giraffes, waterbucks, waterfowl",
        )

        packages_data = [
            {
                "package_code": "SS-REAL-001",
                "title": "5 Days / 4 Nights Coastal Exploration",
                "description": (
                    "A birding and herping focused coastal exploration covering Arabuko Sokoke "
                    "Forest, Mida Creek, Gede Ruins, Watamu Snake Farm and the white sandy beaches "
                    "of the Indian Ocean. Valid for Kenya residents. Price is per person sharing, in KES."
                ),
                "duration_days": 5,
                "base_price": 26673,
                "included_services": (
                    "Park & site entry fees (Watamu Snake Farm, Gede Ruins, Arabuko Sokoke, Mida Creek, "
                    "Watamu Marine Park), specialist birding/herping guide, accommodation (4 nights), "
                    "ground transportation, daily meals"
                ),
                "excluded_services": "Snorkeling costs, extra activities, items of personal use, tips",
                "locations": [watamu],
                "itinerary": [
                    ("Naivasha - Watamu", "Early departure, stop at Mtito Andei for lunch, arrive Watamu Snake Park Camp site, dinner and overnight.", watamu),
                    ("Watamu Snake Farm and Gede Ruins", "Coastal herping at Watamu Snake Farm, explore Gede Ruins, back to camp for dinner and overnight.", watamu),
                    ("Watamu - Arabuko Sokoke Forest", "Morning birdwalk in Arabuko Sokoke Forest (Malindi pipit, Sokoke pipit, elephant shrew), afternoon exploring the birds of Mida Creek, optional beach swimming.", watamu),
                    ("Watamu - Coral Garden Walk and Marine Park", "Coral garden and reef exploration, Watamu Marine Park visit with optional water activities.", watamu),
                    ("Watamu - Naivasha", "Early Arocha Kenya birdwalk, then drive back to Naivasha with lunch stops at Emali/Mtito Andei.", watamu),
                ],
            },
            {
                "package_code": "SS-REAL-002",
                "title": "7 Days / 6 Nights Best of Kenya Safari (4 PAX)",
                "description": (
                    "Best of Kenya safari for 2 adults + 2 children (2-11/17), covering Masai Mara "
                    "National Reserve, Lake Nakuru National Park, a walking safari on Crescent Island "
                    "and the Olkaria Geothermal Spa in Hell's Gate. Starts and ends at JKIA. "
                    "Price is per person sharing, in USD."
                ),
                "duration_days": 7,
                "base_price": 2929,
                "included_services": (
                    "Full board accommodation, entry fees to all parks/reserves visited, guided game "
                    "drives in a 4x4 Land Cruiser, Olkaria Geothermal Spa, English speaking guide, "
                    "meals as stated, Masai Mara village tour, airport & hotel/lodge transfers, "
                    "drinking water, boat ride in Lake Naivasha"
                ),
                "excluded_services": "Balloon ride in Masai Mara, all optional/extra activities, items of personal use and tips",
                "locations": [nairobi, masai_mara, lake_nakuru, naivasha],
                "itinerary": [
                    ("Airport Transfer - Nairobi", "Pickup at JKIA, drop off at Sarova Panafric. Optional visit to Nairobi National Museum and Snake Park. Dinner and overnight.", nairobi),
                    ("Nairobi - Masai Mara National Reserve", "Early breakfast, scenic stop at the Great Rift Valley viewpoint en route, arrive Jambo Mara Lodge for lunch, evening game drive, dinner and overnight.", masai_mara),
                    ("Masai Mara National Reserve - Full Day Game Drive", "Early morning game drive through the Mara's acacia plains, picnic lunch in the savannah, pass by Mara River to check for the wildebeest migration, dinner and overnight.", masai_mara),
                    ("Masai Mara - Lake Nakuru National Park", "Breakfast, drive to Lake Nakuru National Park (optional Masai Village visit en route), afternoon game drive to see white/black rhino and Grey Crowned Crane, dinner and overnight.", lake_nakuru),
                    ("Lake Nakuru - Olkaria Geothermal Spa", "Rest day inside Hell's Gate National Park at the Olkaria Geothermal Spa, with swimmable hot springs for adults and children. Dinner and overnight.", naivasha),
                    ("Crescent Island - Giraffe Center", "Checkout and walking safari on Naivasha's Crescent Island (boat ride to the island), drive back to Nairobi, optional Giraffe Center visit. Dinner and overnight.", naivasha),
                    ("Airport Transfer", "Breakfast, checkout, transfer to the airport or desired location, with an optional KICC and Masai Market visit.", nairobi),
                ],
            },
            {
                "package_code": "SS-REAL-003",
                "title": "3 Days / 2 Nights Crescent Island, Hell's Gate & Olkaria Spa",
                "description": (
                    "A short Naivasha getaway covering Crescent Island, Hell's Gate National Park and "
                    "the Olkaria Geothermal Spa. Starts and ends in Kisumu. Price is per person sharing, in KES."
                ),
                "duration_days": 3,
                "base_price": 17160,
                "included_services": (
                    "Crescent Island entry fees, Olkaria Geothermal Spa entry, Hell's Gate National Park "
                    "entry fees, boat transfers to/from Crescent Island, accommodation at Fisherman's Camp, "
                    "full time professional tour guide, mineral drinking water"
                ),
                "excluded_services": "Meals as stated, transport/transfers between destinations except boat transfers, extra activities, tips, items of personal use and laundry",
                "locations": [naivasha],
                "itinerary": [
                    ("Kisumu - Naivasha", "Depart Kisumu for Naivasha, check in to camp, dinner and overnight.", naivasha),
                    ("Crescent Island - Hell's Gate & Olkaria Spa", "Breakfast at Fisherman's Restaurant, boat over to Crescent Island for a walking safari among zebras, giraffes and waterbucks; afternoon at the Olkaria Geothermal Spa in Hell's Gate with optional rock climbing/cycling. Dinner and overnight.", naivasha),
                    ("Naivasha - Kisumu", "Optional morning boat ride to explore the birds of Lake Naivasha, then depart for Kisumu (optional extension to Nairobi's snake park, museum and giraffe centre).", naivasha),
                ],
            },
        ]

        for data in packages_data:
            itinerary_days = data.pop("itinerary")
            locations = data.pop("locations")
            package, created = SafariPackage.objects.update_or_create(
                package_code=data["package_code"],
                defaults=data,
            )
            package.locations.set(locations)

            for day_number, (title, description, loc) in enumerate(itinerary_days, start=1):
                PackageItinerary.objects.update_or_create(
                    package=package,
                    day_number=day_number,
                    defaults={
                        "title": f"Day {day_number}: {title}",
                        "description": description,
                        "location": loc,
                    },
                )

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"- {action}: {package.title} ({package.package_code})"))

        self.stdout.write(self.style.SUCCESS("Real client packages seeded."))
