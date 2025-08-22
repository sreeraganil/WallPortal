from django.http import HttpResponse

def robots_txt(request):
    content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /upload/
    Allow: /

    Sitemap: https://flicker-web.onrender.com/sitemap.xml
    """
    return HttpResponse(content, content_type="text/plain")
