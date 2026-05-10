from django.core.management.base import BaseCommand
from inventory.models import Page, Module, Permission

class Command(BaseCommand):
    help = 'Seeds the database with sitemap pages and permission matrix'

    def handle(self, *args, **options):
        self.stdout.write('Seeding pages...')
        pages_data = [
            # Public
            ('P01', 'Home', 'Hero, featured destinations, testimonials, luxury CTAs', 'PUBLIC'),
            ('P02', 'About Us', 'Story, team, certifications, awards, sustainability pledge', 'PUBLIC'),
            ('P03', 'Destinations', 'Kenya, Tanzania, Rwanda, Uganda, Zanzibar — filterable grid', 'PUBLIC'),
            ('P04', 'Destination Detail', 'Wildlife, seasons, packages, gallery, related gear', 'PUBLIC'),
            ('P05', 'Packages', 'Browse all tour packages with filters (duration, budget, style)', 'PUBLIC'),
            ('P06', 'Package Detail', 'Itinerary, inclusions, pricing, reviews, gear cross-sell', 'PUBLIC'),
            ('P07', 'Contact', 'Form, live chat, WhatsApp, office locations, FAQ', 'PUBLIC'),
            ('P08', 'Blog / Journal', 'Safari tips, wildlife news, seasonal guides', 'PUBLIC'),
            ('P09', 'Sign In / Register', 'Auth portal — social login, email, forgot password', 'PUBLIC'),
            ('P10', 'Trip Documents', 'Download vouchers, preparation guides, and legal forms', 'USER'),
            # E-commerce
            ('E01', 'Shop Home', 'Featured products, categories, seasonal promos, bundles', 'PUBLIC'),
            ('E02', 'Product Listing', 'Filterable grid — gear, clothing, luxury add-ons, bundles', 'PUBLIC'),
            ('E03', 'Product Detail', 'Gallery, specs, size guide, related products, reviews', 'PUBLIC'),
            ('E04', 'Shopping Cart', 'Dedicated cart management, bundle savings, and upsells', 'PUBLIC'),
            ('E05', 'Checkout — Details', 'Shipping address, currency selector (USD/EUR/KES/GBP)', 'USER'),
            ('E06', 'Checkout — Payment', 'Credit card, M-Pesa, PayPal, bank transfer, 3D Secure', 'USER'),
            ('E07', 'Order Confirmation', 'Summary, next steps, trip documents', 'PUBLIC'),
            ('E08', 'Bundle Builder', 'Custom tour + gear bundles, dynamic savings calculator', 'PUBLIC'),
            # User Dashboard
            ('U01', 'My Dashboard', 'Overview: upcoming trips, orders, loyalty points, notifications', 'USER'),
            ('U02', 'My Bookings', 'Active, upcoming, past bookings; cancel/modify; documents', 'USER'),
            ('U03', 'Order History', 'Shop orders, invoices, returns, tracking', 'USER'),
            ('U04', 'Saved / Wishlist', 'Saved packages, products, and custom itineraries', 'USER'),
            ('U05', 'Loyalty & Rewards', 'Points balance, tier status, redemption history', 'USER'),
            ('U06', 'Profile & Preferences', 'Personal info, currency, language, notification prefs', 'USER'),
            # Sub-Admin
            ('A01', 'Admin Dashboard', 'KPIs: bookings today, revenue, inventory alerts, new orders', 'SUBADMIN'),
            ('A02', 'Destinations Manager', 'Add/edit/delete destinations, upload media, set seasons', 'SUBADMIN'),
            ('A03', 'Packages Manager', 'Create/edit packages, itineraries, pricing tiers, availability', 'SUBADMIN'),
            ('A04', 'Bookings Manager', 'View/process bookings, assign guides, send documents', 'SUBADMIN'),
            ('A05', 'Products Manager', 'Add/edit/delete shop products, set prices, manage variants', 'SUBADMIN'),
            ('A06', 'Inventory Manager', 'Stock levels, low-stock alerts, restock requests', 'SUBADMIN'),
            ('A07', 'Content / Blog', 'Write/publish/schedule blog posts and travel guides', 'SUBADMIN'),
            ('A08', 'Sales Reports', 'View assigned region reports — no full system access', 'SUBADMIN'),
            # Super Admin
            ('S01', 'Master Dashboard', 'Full KPI overview: revenue, bookings, orders, users, alerts', 'SUPERADMIN'),
            ('S02', 'User Management', 'Create/edit/delete all users; assign/revoke roles', 'SUPERADMIN'),
            ('S03', 'Roles & Permissions', 'Define custom roles, assign permission sets per module', 'SUPERADMIN'),
            ('S04', 'Analytics & Reporting', 'Revenue, conversion, geographic, seasonal analytics', 'SUPERADMIN'),
            ('S05', 'Promotions Engine', 'Create promo codes, flash sales, seasonal campaigns', 'SUPERADMIN'),
            ('S06', 'Multi-Currency Settings', 'FX rates, payment gateway config, tax rules per region', 'SUPERADMIN'),
            ('S07', 'System Settings', 'Site config, email templates, integrations, API keys', 'SUPERADMIN'),
            ('S08', 'Audit Logs', 'Full audit trail: who did what, when, with IP logging', 'SUPERADMIN'),
        ]

        for code, name, purpose, access in pages_data:
            Page.objects.get_or_create(code=code, defaults={'name': name, 'purpose': purpose, 'access_level': access})

        self.stdout.write('Seeding modules and permissions...')
        matrix = [
            # Module Name, Visitor (v,c,e,d,note), User, SubAdmin, SuperAdmin
            ('Browse Destinations & Packages', (True,False,False,False,''), (True,False,False,False,''), (True,False,False,False,''), (True,False,False,False,'')),
            ('Browse Shop / Products', (True,False,False,False,''), (True,False,False,False,''), (True,False,False,False,''), (True,False,False,False,'')),
            ('Checkout / Purchase', (False,False,False,False,'→ Auth'), (True,True,False,False,''), (True,True,False,False,''), (True,True,True,True,'')),
            ('Book a Safari Package', (False,False,False,False,'→ Auth'), (True,True,False,False,''), (True,True,True,False,''), (True,True,True,True,'')),
            ('View My Bookings', (False,False,False,False,''), (True,False,True,False,'Modify'), (True,False,True,False,''), (True,True,True,True,'')),
            ('Manage Destinations', (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,''), (True,True,True,True,'')),
            ('Manage Packages', (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,''), (True,True,True,True,'')),
            ('Manage Products (Shop)', (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,''), (True,True,True,True,'')),
            ('View All Bookings', (False,False,False,False,''), (False,False,False,False,''), (True,False,True,False,'Process'), (True,True,True,True,'')),
            ('View All Orders', (False,False,False,False,''), (False,False,False,False,''), (True,False,False,False,''), (True,True,True,True,'')),
            ('Manage Inventory', (False,False,False,False,''), (False,False,False,False,''), (True,False,True,False,'Update'), (True,True,True,True,'')),
            ('View Analytics (Limited)', (False,False,False,False,''), (False,False,False,False,''), (True,False,False,False,'Region only'), (True,True,True,True,'')),
            ('Full Analytics & Revenue Reports', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'Export')),
            ('Create / Manage Promotions', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'')),
            ('User Management (All Users)', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'')),
            ('Assign Roles & Permissions', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'')),
            ('Multi-Currency Configuration', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'')),
            ('System Settings', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,True,True,True,'')),
            ('Audit Logs', (False,False,False,False,''), (False,False,False,False,''), (False,False,False,False,''), (True,False,False,False,'')),
        ]

        roles = ['VISITOR', 'USER', 'SUBADMIN', 'SUPERADMIN']

        for entry in matrix:
            module_name = entry[0]
            module, _ = Module.objects.get_or_create(name=module_name)
            
            for i, role in enumerate(roles):
                perms = entry[i+1]
                Permission.objects.update_or_create(
                    module=module,
                    role=role,
                    defaults={
                        'can_view': perms[0],
                        'can_create': perms[1],
                        'can_edit': perms[2],
                        'can_delete': perms[3],
                        'special_notes': perms[4]
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded sitemap data.'))
