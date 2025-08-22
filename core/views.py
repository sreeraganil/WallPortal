from django.http import HttpResponse

def robots_txt(request):
    content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /upload/
    Allow: /

    Sitemap: https://gem4k.onrender.com/sitemap.xml
    """
    return HttpResponse(content, content_type="text/plain")
