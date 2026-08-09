import pytest
from django_crawl import CrawlClient, crawl


@pytest.mark.django_db
def test_public_pages_have_no_broken_links():
    """Walk the anonymous site in-process: no 5xx, no dead links or assets."""
    crawl("/", client=CrawlClient())


@pytest.mark.django_db
def test_authenticated_pages_have_no_broken_links(user):
    client = CrawlClient()
    client.force_login(user)

    crawl("/", client=client)
