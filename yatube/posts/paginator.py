from django.core.paginator import Paginator

from .constanta import COUNT_POSTS


def paginator_posts(request, posts):
    paginator = Paginator(posts, COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
