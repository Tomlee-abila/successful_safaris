import random
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils.text import slugify
from faker import Faker
from destinations.models import Destination, SafariLocation, Accommodation
from packages.models import SafariPackage, PackageItinerary
from users.models import UserProfile
from bookings.models import Booking, Traveler, Payment
from shop.models import ProductCategory, Product, Order, OrderItem
from crm.models import Inquiry, Review, TripDocument
from blog.models import BlogCategory, BlogPost
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import datetime

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the entire safari business domain with realistic demo data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing business data before seeding',
        )

    def handle(self, *args, **kwargs):
        self._image_cache = {}
        if kwargs.get('clear'):
            self.stdout.write(self.style.WARNING("WARNING: This will delete ALL business data (Destinations, Packages, Bookings, Orders, Products, etc.)"))
            confirm = input("Are you sure you want to proceed? Type 'YES' to continue: ")
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR("Seeding cancelled."))
                return

            self.stdout.write("Clearing existing business data...")
            self.clear_data()
            self.stdout.write(self.style.SUCCESS("Cleanup complete."))

        self.stdout.write("--- Phase 1: Core Data (Roles & Users) ---")
        self.seed_core()
        
        self.stdout.write("\n--- Phase 2: Catalog Data (Destinations, Packages, Products) ---")
        destinations, locations, packages = self.seed_catalog()
        
        self.stdout.write("\n--- Phase 3: Transactional Data (Bookings, Payments, Orders) ---")
        self.seed_transactions(packages)
        
        self.stdout.write("\n--- Phase 4: Content & CRM (Blog, Reviews, Inquiries) ---")
        self.seed_content_and_crm(destinations, packages)
        
        self.stdout.write("\n" + self.style.SUCCESS("Successfully seeded the Successful Safaris business domain!"))

    def download_image(self, url, filename):
        """Helper to download image and return ContentFile with caching"""
        if url in self._image_cache:
            return ContentFile(self._image_cache[url], name=filename)

        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                self._image_cache[url] = response.content
                return ContentFile(response.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to download image {url}: {e}"))
        return None

    def clear_data(self):
        # Clear in reverse order of dependencies
        Review.objects.all().delete()
        TripDocument.objects.all().delete()
        Inquiry.objects.all().delete()
        BlogPost.objects.all().delete()
        BlogCategory.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        ProductCategory.objects.all().delete()
        Payment.objects.all().delete()
        Traveler.objects.all().delete()
        Booking.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_staff=False).delete()
        SafariPackage.objects.all().delete()
        Accommodation.objects.all().delete()
        SafariLocation.objects.all().delete()
        Destination.objects.all().delete()

    def seed_core(self):
        self.seed_groups()
        users = self.seed_users()
        return users

    def seed_catalog(self):
        destinations = self.seed_destinations()
        locations = self.seed_locations(destinations)
        self.seed_accommodations(locations)
        packages = self.seed_packages(locations)
        self.seed_shop()
        return destinations, locations, packages

    def seed_transactions(self, packages):
        users = User.objects.filter(groups__name='Customer')
        bookings = self.seed_bookings(users, packages)
        self.seed_travelers_and_payments(bookings)

    def seed_content_and_crm(self, destinations, packages):
        users = User.objects.filter(is_staff=False)
        self.seed_content(users, packages, destinations)

    def seed_groups(self):
        roles = [
            'Visitor', 'Customer', 'Travel Consultant', 'Operations Officer',
            'Regional Manager', 'Finance Officer', 'Content Manager', 'Sub Admin', 'Super Admin'
        ]
        for role in roles:
            Group.objects.get_or_create(name=role)
        self.stdout.write("- Groups/Roles seeded.")

    def seed_destinations(self):
        countries = [
            ("Kenya", "The jewel of East Africa, home to the Masai Mara and diverse wildlife.", "1535941339077-2dd1c7963098"),
            ("Tanzania", "Famous for the Serengeti, Ngorongoro Crater, and Mount Kilimanjaro.", "1547970810-dc1eac37d174"),
            ("Rwanda", "Land of a Thousand Hills, premier destination for Gorilla trekking.", "1530126483408-aa533e55bdb2"),
            ("Uganda", "The Pearl of Africa, offering unique forest and savannah experiences.", "1564760055775-d63b17a55c44"),
            ("Botswana", "Pristine wilderness featuring the Okavango Delta and Chobe.", "1516426122078-c23e76319801"),
            ("Namibia", "Dramatic desert landscapes and the world-class Etosha National Park.", "1519098901920-285444123594"),
            ("South Africa", "A blend of sophisticated cities and world-renowned game reserves.", "1516026672322-bc52d61a55d5"),
            ("Zambia", "The birthplace of walking safaris and the mighty Victoria Falls.", "1586861635167-e5223aadc9fe")
        ]
        dest_objects = []
        for name, desc, photo_id in countries:
            dest, created = Destination.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'best_travel_season': "June to October (Dry Season)",
                    'visa_information': "Visa required for most nationalities, e-visas available.",
                    'health_requirements': "Yellow Fever certificate required if traveling from endemic zones.",
                    'featured_wildlife': "The Big Five"
                }
            )
            if created or not dest.hero_image:
                img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=1600&q=80"
                image_file = self.download_image(img_url, f"{slugify(name)}_hero.jpg")
                if image_file:
                    dest.hero_image.save(f"{slugify(name)}_hero.jpg", image_file)
            dest_objects.append(dest)
        self.stdout.write(f"- {len(dest_objects)} Destinations seeded.")
        return dest_objects

    def seed_locations(self, destinations):
        location_photos = [
            "1501705820400-98317e08272f", "1547234935-80c7145ec969", "1523800378286-dae1f0dae641",
            "1516426122078-c23e76319801", "1549366021-9f758f090ce2", "1518709268805-4e9042af9f23",
            "157555095922c-a3ff69d273d2", "1534067783941-51c9c23ea33c", "1541414779316-956a5014b13d"
        ]
        location_data = {
            "Kenya": ["Masai Mara National Reserve", "Amboseli National Park", "Tsavo National Park", "Samburu Reserve"],
            "Tanzania": ["Serengeti National Park", "Ngorongoro Conservation Area", "Tarangire National Park", "Zanzibar Archipelago"],
            "Rwanda": ["Volcanoes National Park", "Akagera National Park", "Nyungwe Forest"],
            "Uganda": ["Bwindi Impenetrable Forest", "Queen Elizabeth National Park", "Murchison Falls"],
            "Botswana": ["Okavango Delta", "Chobe National Park", "Central Kalahari"],
            "Namibia": ["Etosha National Park", "Sossusvlei", "Damaraland"],
            "South Africa": ["Kruger National Park", "Sabi Sands", "Phinda Private Game Reserve"],
            "Zambia": ["South Luangwa", "Lower Zambezi", "Victoria Falls"]
        }
        loc_objects = []
        for dest in destinations:
            names = location_data.get(dest.name, ["Main Park"])
            for name in names:
                loc, created = SafariLocation.objects.get_or_create(
                    destination=dest,
                    name=name,
                    defaults={
                        'description': fake.paragraph(nb_sentences=5),
                        'activities': "Game Drives, Guided Walks, Hot Air Ballooning",
                        'wildlife': "Lions, Leopards, Elephants, Buffaloes, Rhinos",
                        'latitude': fake.latitude(),
                        'longitude': fake.longitude()
                    }
                )
                if created or not loc.featured_image:
                    photo_id = random.choice(location_photos)
                    img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&q=80"
                    image_file = self.download_image(img_url, f"{slugify(name)}.jpg")
                    if image_file:
                        loc.featured_image.save(f"{slugify(name)}.jpg", image_file)
                loc_objects.append(loc)
        self.stdout.write(f"- {len(loc_objects)} Locations seeded.")
        return loc_objects

    def seed_accommodations(self, locations):
        accommodation_photos = [
            "1582719508461-905c673771fd", "1571896349842-33c89424de2d", "1566073771259-6a8506099945",
            "1542314831-068cd1dbfeeb", "1520250497591-112f2f40a3f4", "1564501049412-61c2a3083791",
            "1596394516093-501ba68a0ba6", "1445013117565-d01869894e43"
        ]
        types = ['LODGE', 'CAMP', 'VILLA', 'HOTEL']
        acc_objects = []
        for loc in locations:
            for i in range(2): # 2 accommodations per location
                name = f"{fake.company()} {random.choice(['Lodge', 'Camp', 'Retreat', 'Sanctuary'])}"
                acc = Accommodation.objects.create(
                    location=loc,
                    name=name,
                    type=random.choice(types),
                    description=fake.paragraph(nb_sentences=3),
                    capacity=random.randint(10, 50),
                    nightly_rate=random.randint(400, 2500),
                    amenities="Wi-Fi, Pool, Spa, Private Deck, All-inclusive dining",
                )
                photo_id = random.choice(accommodation_photos)
                img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&q=80"
                image_file = self.download_image(img_url, f"acc-{slugify(name)}.jpg")
                if image_file:
                    acc.featured_image.save(f"acc-{slugify(name)}.jpg", image_file)
                acc_objects.append(acc)
        self.stdout.write(f"- {len(acc_objects)} Accommodations seeded.")
        return acc_objects

    def seed_packages(self, locations):
        package_photos = [
            "1516026672322-bc52d61a55d5", "1547970810-dc1eac37d174", "1541414779316-956a5014b13d",
            "1511497584788-8767fe7d98ee", "1523800378286-dae1f0dae641", "1535941339077-2dd1c7963098",
            "1534067783941-51c9c23ea33c", "1564760055775-d63b17a55c44"
        ]
        packages = []
        for i in range(30):
            locs = random.sample(locations, k=random.randint(2, 4))
            title = f"{random.choice(['Ultimate', 'Grand', 'Exclusive', 'Classic'])} {locs[0].destination.name} Safari"
            package = SafariPackage.objects.create(
                package_code=f"SS-PKG-{i+1:03}",
                title=title,
                description=fake.paragraph(nb_sentences=6),
                duration_days=random.randint(4, 14),
                base_price=random.randint(2000, 10000),
                included_services="Accommodation, Meals, Guided Game Drives, Airport Transfers",
                excluded_services="International Flights, Personal Insurance, Gratuities",
            )
            package.locations.set(locs)
            
            photo_id = random.choice(package_photos)
            img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&q=80"
            image_file = self.download_image(img_url, f"pkg-{package.package_code}.jpg")
            if image_file:
                package.featured_image.save(f"pkg-{package.package_code}.jpg", image_file)

            # Seed Itinerary
            for day in range(1, package.duration_days + 1):
                PackageItinerary.objects.create(
                    package=package,
                    day_number=day,
                    title=f"Day {day}: {fake.sentence(nb_words=4)}",
                    description=fake.paragraph(nb_sentences=3),
                    location=random.choice(locs)
                )
            packages.append(package)
        self.stdout.write(f"- {len(packages)} Safari Packages seeded.")
        return packages

    def seed_users(self):
        user_objects = []
        customer_group = Group.objects.get(name='Customer')
        
        # 1. Create Staff Test Accounts
        staff_roles = [
            ('subadmin', 'Sub Admin'),
            ('superadmin', 'Super Admin'),
        ]
        for username, group_name in staff_roles:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@successfulsafaris.com",
                    password='password123',
                    is_staff=True,
                    is_superuser=(username == 'superadmin')
                )
                user.groups.add(Group.objects.get(name=group_name))
                UserProfile.objects.create(user=user)
                self.stdout.write(f"  - Staff account created: {username}")

        # 2. Create Demo Customers
        for i in range(30):
            profile = fake.profile()
            username = profile['username']
            if User.objects.filter(username=username).exists():
                username += str(i)
            user = User.objects.create_user(
                username=username,
                email=profile['mail'],
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            user.groups.add(customer_group)
            
            profile_obj = UserProfile.objects.create(
                user=user,
                phone=fake.phone_number(),
                nationality=fake.country(),
                passport_number=fake.bothify(text='??#######'),
                loyalty_tier=random.choice(['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']),
                loyalty_points=random.randint(0, 5000),
            )
            img_url = f"https://i.pravatar.cc/150?u={username}"
            image_file = self.download_image(img_url, f"{username}.jpg")
            if image_file:
                profile_obj.avatar.save(f"{username}.jpg", image_file)
            user_objects.append(user)
        self.stdout.write(f"- {len(user_objects)} Users and Profiles seeded.")
        return user_objects

    def seed_bookings(self, users, packages):
        statuses = ['DRAFT', 'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']
        booking_objects = []
        for i in range(20):
            user = random.choice(users)
            package = random.choice(packages)
            booking = Booking.objects.create(
                booking_number=f"SS-BK-{i+1:05}",
                customer=user,
                package=package,
                start_date=timezone.now().date() + datetime.timedelta(days=random.randint(-365, 365)),
                total_amount=package.base_price * random.randint(1, 4),
                status=random.choice(statuses)
            )
            booking_objects.append(booking)
        self.stdout.write(f"- {len(booking_objects)} Bookings seeded.")
        return booking_objects

    def seed_travelers_and_payments(self, bookings):
        payment_methods = ['CARD', 'BANK_TRANSFER', 'MOBILE_MONEY']
        payment_statuses = ['PENDING', 'PARTIAL', 'COMPLETED', 'REFUNDED']
        for b in bookings:
            # Travelers
            num_travelers = random.randint(1, 4)
            for j in range(num_travelers):
                Traveler.objects.create(
                    booking=b,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    passport_number=fake.bothify(text='??#######'),
                    nationality=fake.country(),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    is_primary=(j == 0)
                )
            # Payments
            if b.status != 'DRAFT':
                Payment.objects.create(
                    booking=b,
                    amount=b.total_amount if b.status in ['CONFIRMED', 'COMPLETED'] else b.total_amount / 2,
                    method=random.choice(payment_methods),
                    status='COMPLETED' if b.status in ['CONFIRMED', 'COMPLETED'] else random.choice(payment_statuses),
                    transaction_id=fake.uuid4()
                )
        self.stdout.write("- Travelers and Payments seeded.")

    def seed_shop(self):
        shop_photos = {
            "Clothing": ["1534030347204-57c86bf15175", "1520639832093-87586ca95b35"],
            "Boots": ["1560761303-2197ad667362", "1520639832093-87586ca95b35"],
            "Backpacks": ["1553062407-98eeb64c6a62", "1523275335684-37898b6baf30"],
            "Binoculars": ["1523275335684-37898b6baf30"],
            "Cameras": ["1516035069174-06c58899c591", "1526170375885-cf044a7243ee"],
            "Travel Accessories": ["1523275335684-37898b6baf30"],
            "Camping Gear": ["1504280390367-361c6d9f38f4", "1523275335684-37898b6baf30"]
        }
        cats = ["Clothing", "Boots", "Backpacks", "Binoculars", "Cameras", "Travel Accessories", "Camping Gear"]
        cat_objects = []
        for c in cats:
            cat, _ = ProductCategory.objects.get_or_create(name=c, slug=slugify(c))
            cat_objects.append(cat)
        
        products = []
        for i in range(40):
            cat = random.choice(cat_objects)
            name = f"{fake.word().capitalize()} {cat.name[:-1] if cat.name.endswith('s') else cat.name}"
            prod = Product.objects.create(
                category=cat,
                sku=f"SS-PROD-{i+1:04}",
                name=name,
                description=fake.paragraph(nb_sentences=4),
                price=random.randint(50, 3000),
                stock_quantity=random.randint(0, 100),
                low_stock_threshold=random.randint(5, 15),
                is_active=True
            )
            photo_list = shop_photos.get(cat.name, ["1523275335684-37898b6baf30"])
            photo_id = random.choice(photo_list)
            img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=800&q=80"
            image_file = self.download_image(img_url, f"prod-{slugify(name)}.jpg")
            if image_file:
                prod.image.save(f"prod-{slugify(name)}.jpg", image_file)
            products.append(prod)
        self.stdout.write(f"- {len(products)} Shop Products seeded.")

    def seed_content(self, users, packages, destinations):
        blog_photos = ["1516026672322-bc52d61a55d5", "1547970810-dc1eac37d174", "1534067783941-51c9c23ea33c", "1501705820400-98317e08272f"]
        # Blog
        b_cats = ["Wildlife", "Travel Tips", "Luxury Travel", "Conservation", "Photography"]
        for c in b_cats:
            cat, _ = BlogCategory.objects.get_or_create(name=c, slug=slugify(c))
            for i in range(5):
                title = fake.sentence(nb_words=6)
                post = BlogPost.objects.create(
                    title=title,
                    slug=slugify(title),
                    author=random.choice(users),
                    category=cat,
                    content=fake.paragraphs(nb=5),
                    is_published=True
                )
                photo_id = random.choice(blog_photos)
                img_url = f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=1200&q=80"
                image_file = self.download_image(img_url, f"blog-{slugify(title)}.jpg")
                if image_file:
                    post.featured_image.save(f"blog-{slugify(title)}.jpg", image_file)
        self.stdout.write("- Blog posts seeded.")

        # Reviews
        package_type = ContentType.objects.get_for_model(SafariPackage)
        for p in random.sample(packages, k=15):
            for _ in range(3):
                Review.objects.create(
                    user=random.choice(users),
                    rating=random.randint(4, 5),
                    comment=fake.paragraph(),
                    content_type=package_type,
                    object_id=p.id
                )
        self.stdout.write("- Reviews seeded.")

        # Inquiries
        for _ in range(30):
            Inquiry.objects.create(
                name=fake.name(),
                email=fake.email(),
                subject=fake.sentence(nb_words=4),
                message=fake.paragraph(),
                is_resolved=random.choice([True, False])
            )
        self.stdout.write("- CRM Inquiries seeded.")
