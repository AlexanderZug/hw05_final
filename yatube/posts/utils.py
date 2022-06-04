from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, post_list):
    pages_paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    return pages_paginator.get_page(request.GET.get('page'))
