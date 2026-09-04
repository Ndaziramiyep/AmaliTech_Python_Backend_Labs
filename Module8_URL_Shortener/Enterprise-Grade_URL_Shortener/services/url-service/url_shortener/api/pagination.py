from rest_framework.pagination import PageNumberPagination


class UrlPagination(PageNumberPagination):
    """Paginates URL list responses at 20 per page, overridable via ?page_size= up to 100."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
