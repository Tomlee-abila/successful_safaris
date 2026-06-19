from django.shortcuts import render
from .models import BlogPost, BlogCategory
from shop.utils import get_cart
from core.decorators import permission_required

@permission_required('Browse Blog & Content')
def blog(request):
    # Staff see all, public see only published
    if request.user.is_staff:
        posts = BlogPost.objects.all().order_by('-created_at')
    else:
        posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    
    categories = BlogCategory.objects.all()
    
    context = {
        'posts': posts,
        'categories': categories,
        'cart': get_cart(request),
    }
    return render(request, 'blog.html', context)
