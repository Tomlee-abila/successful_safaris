# Project Instructions: Successful Luxury Safaris

## Architecture Mandates
- **Modular Apps:** Always use domain-specific apps (e.g., `bookings`, `shop`) instead of putting everything in `core`.
- **Data-Driven UI:** Frontend templates must fetch data from the models. Avoid hardcoding content in HTML.
- **RBAC Enforcement:** All views must respect the `inventory.Permission` matrix. Use decorators or mixins to enforce this.
- **REST First:** For complex frontend interactions (e.g., cart, booking customizer), prefer using DRF endpoints.

## Tech Stack
- **Backend:** Django 6.0.5, Django REST Framework.
- **Frontend:** Server-side rendered Django Templates with Vanilla CSS.
- **Design System:** 
  - Gold (`#C9A84C`)
  - Deep Green (`#1A3A2A`)
  - Fonts: *Playfair Display*, *Inter*, *Cormorant Garamond*.

## Development Workflow
1. **Migrations:** Always run `python manage.py makemigrations` and `migrate` after model changes.
2. **Seeding:** Update `seed_business.py` if new critical entities are added. Use `python manage.py seed_business --clear` for a clean state.
3. **Validation:** Run `python deep_qa.py` to ensure no regressions in routing or API stability.
