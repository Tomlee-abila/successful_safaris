from shop.models import Cart, CartItem

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge anonymous cart if it exists
        session_key = request.session.session_key
        if session_key:
            anon_cart = Cart.objects.filter(session_key=session_key).first()
            if anon_cart and anon_cart != cart:
                for item in anon_cart.items.all():
                    user_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                    if not created:
                        user_item.quantity += item.quantity
                        user_item.save()
                    else:
                        user_item.quantity = item.quantity
                        user_item.save()
                anon_cart.delete()
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart
