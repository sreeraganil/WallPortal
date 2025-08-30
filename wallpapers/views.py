from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils.text import slugify
from .models import Wallpaper
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import requests
from django.contrib import messages
from django.contrib.auth import logout
from xml.sax.saxutils import escape # Import the escape function


from django.urls import reverse

def home(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()
    res = request.GET.get("res", "").strip()
    device = request.GET.get("device", "").strip()
    sort = request.GET.get("sort", "date").strip()  # new

    qs = Wallpaper.objects.all()

    count = qs.count()
    size = qs.aggregate(total_size=Sum('size_bytes'))['total_size'] 

    # Filtering
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(category__icontains=q) |
            Q(tags__icontains=q)
        )
    if cat:
        qs = qs.filter(category__iexact=cat)
    if res:
        if res.lower() == '4k':
            qs = qs.filter(Q(width__gte=3840) | Q(height__gte=2160))
        elif res.lower() == '8k':
            qs = qs.filter(Q(width__gte=7680) | Q(height__gte=4320))
        else:
            qs = qs.filter(resolution_label__iexact=res)
    if device:
        qs = qs.filter(device=device)

    # Sorting
    if sort == "downloads":
        qs = qs.order_by("-downloads")
    elif sort == "featured":
        qs = qs.filter(is_featured=True).order_by("-created_at")
    else:  # default = date
        qs = qs.order_by("-created_at")

    # Pagination
    paginator = Paginator(qs, 24)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    return render(
        request,
        "wallpapers/home.html",
        {
            "page_obj": page_obj,
            "q": q,
            "cat": cat,
            "res": res,
            "device": device,
            "sort": sort,  # send to template
            "categories": Wallpaper.CATEGORY_CHOICES,
            "count": count,
            "size": size
        }
    )

def download(request, slug):
    wp = get_object_or_404(Wallpaper, slug=slug)
    wp.increment_downloads()

    # resolution from query (?res=4k, ?res=hd, etc.)
    res = request.GET.get("res", "").lower()

    transformations = {
        "hd": {"width": 1920, "height": 1080, "crop": "fill"},
        "2k": {"width": 2560, "height": 1440, "crop": "fill"},
        "4k": {"width": 3840, "height": 2160, "crop": "fill"},
        "mobile": {"width": 1080, "height": 2400, "crop": "fill"},
    }

    options = transformations.get(res)
    if options:
        # Generate transformed URL with Cloudinary
        download_url, _ = cloudinary_url(
            wp.drive_file_id,
            transformation=[options],
            flags="attachment"
        )
    else:
        # Default = original
        download_url = wp.download_link.replace("/upload/", "/upload/fl_attachment/")

    # Fetch from Cloudinary and return as response
    r = requests.get(download_url, stream=True)
    file_extension = wp.mime_type.split('/')[-1] if wp.mime_type else 'jpg'
    filename = f"{slugify(wp.title)}_{res or 'original'}.{file_extension}"

    response = HttpResponse(r.content, content_type=f"application/{file_extension}")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@user_passes_test(lambda u: u.is_staff)
def upload(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        category = request.POST.get("category", "")
        device = request.POST.get("device", "")
        tags = request.POST.get("tags", "")
        featured = "featured" in request.POST
        image_file = request.FILES.get("image")
        print(category)

        if not title or not image_file:
            messages.error(request, "Title and Image file are required.")
            return redirect("wallpapers:upload")

        try:
            uploaded = cloudinary.uploader.upload(
                image_file,
                folder="wallpapers",
                resource_type="image"
            )

            width = uploaded.get("width")
            height = uploaded.get("height")
            size_bytes = uploaded.get("bytes", 0)
            img_format = uploaded.get("format", "")

            if not width or not height:
                try:
                    image_file.seek(0)
                    with Image.open(image_file) as img:
                        width, height = img.size
                except Exception as e:
                    print(f"Pillow error getting image dimensions: {e}")

            public_id = uploaded["public_id"]  

            preview_size = {"width": 600, "height": 600, "crop": "limit"}

            if device == "mobile":
                preview_size = {"width": 1000, "height": 1000, "crop": "limit"}

            preview_url, _ = cloudinary_url(
                public_id,
                transformation=[
                    preview_size,
                    {"quality": "auto:low", "fetch_format": "auto"}
                ]
            )

            # Original download URL (full quality, original format)
            download_url = uploaded["secure_url"]

            wp = Wallpaper(
                title=title,
                category=category,
                drive_file_id=public_id,
                view_link=preview_url,
                download_link=download_url,
                mime_type=f"image/{img_format}",
                width=width,
                height=height,
                device=device,
                is_featured=featured,
                tags=tags,
                size_bytes=size_bytes
            )
            
            wp.save()
            messages.success(request, f"'{wp.title}' uploaded successfully!")
            return redirect("wallpapers:detail", slug=wp.slug)
        
        except Exception as e:
            messages.error(request, f"An error occurred during upload: {str(e)}")

    context = {
        "max_size_mb": 10, 
        'categories': Wallpaper.CATEGORY_CHOICES,
        'devices': Wallpaper.DEVICE_CHOICES
    }

    return render(request, "wallpapers/upload.html", context)


def detail(request, slug):
    wp = get_object_or_404(Wallpaper, slug=slug)
    
    related = Wallpaper.objects.filter(
        category=wp.category
    ).exclude(
        slug=wp.slug
    ).order_by('-downloads')[:6]
    
    return render(
        request, 
        "wallpapers/detail.html", 
        {
            "wp": wp,
            "related": related,
            "tags": wp.tags.split(","),
            "aspect_ratio": wp.aspect_ratio
        }
    )



@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_wallpaper(request, slug):
    wp = get_object_or_404(Wallpaper, slug=slug)

    if request.method == "POST":
        # Delete from Cloudinary first
        try:
            if wp.drive_file_id:
                cloudinary.uploader.destroy(wp.drive_file_id, resource_type="image")
        except Exception as e:
            print(f"Cloudinary delete error: {e}")

        wp.delete()
        messages.success(request, f"'{wp.title}' deleted successfully!")
        return redirect("wallpapers:home")

    return redirect("wallpapers:home")




def logout_view(request):
    logout(request)
    return redirect('wallpapers:home')


def about_view(request):
    return render(request, 'pages/about.html')

def privacy_policy_view(request):
    return render(request, 'pages/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'pages/terms_of_service.html')

def contact_view(request):
    return render(request, 'pages/contact.html')




def sitemap(request):
    base_url = request.build_absolute_uri('/')[:-1]
    urls = []

    # Homepage
    urls.append({
        "loc": base_url + reverse("wallpapers:home"),
        "priority": "1.0",
        "changefreq": "daily",
        "images": []
    })

    # Upload page
    urls.append({
        "loc": base_url + reverse("wallpapers:upload"),
        "priority": "0.7",
        "changefreq": "monthly",
        "images": []
    })

    # Wallpaper detail pages
    for wp in Wallpaper.objects.all().iterator():
        image_url = wp.view_link or wp.download_link
        tags = [t.name for t in wp.tags.all()] if hasattr(wp.tags, "all") else []
        seo_keywords = ", ".join(tags[:5]) if tags else "HD, 4K, wallpaper"
        seo_title = f"{wp.title} | {seo_keywords}"
        seo_caption = f"Download {wp.title} in {seo_keywords} resolution from WallPortal."

        urls.append({
            "loc": base_url + reverse("wallpapers:detail", args=[wp.slug]),
            "priority": "0.9",
            "changefreq": "weekly",
            "lastmod": wp.updated_at.strftime("%Y-%m-%d") if hasattr(wp, "updated_at") and wp.updated_at else None,
            "images": [{
                "loc": image_url,
                "title": seo_title,
                "caption": seo_caption
            }] if image_url else []
        })
    
    # Generate XML with image namespace
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    xml += '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'

    for u in urls:
        xml += "  <url>\n"
        xml += f"    <loc>{escape(u['loc'])}</loc>\n"
        if u.get("lastmod"):
            xml += f"    <lastmod>{u['lastmod']}</lastmod>\n"
        xml += f"    <changefreq>{u['changefreq']}</changefreq>\n"
        xml += f"    <priority>{u['priority']}</priority>\n"

        # Add images if available
        for img in u.get("images", []):
            if img.get("loc"):
                xml += "    <image:image>\n"
                xml += f"      <image:loc>{escape(img['loc'])}</image:loc>\n"
                if img.get("title"):
                    xml += f"      <image:title>{escape(img['title'])}</image:title>\n"
                if img.get("caption"):
                    xml += f"      <image:caption>{escape(img['caption'])}</image:caption>\n"
                xml += "    </image:image>\n"

        xml += "  </url>\n"

    xml += "</urlset>"

    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
