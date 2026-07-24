from flask import Blueprint, render_template, Response

from app.utils import content_service as content

main_bp = Blueprint("main", __name__)


@main_bp.route("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /auth/",
        "Disallow: /medicines/cart",
        "Disallow: /medicines/checkout",
        f"Sitemap: {request_root()}sitemap.xml",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap():
    from flask import url_for

    urls = [url_for("main.home", _external=True), url_for("medicines.store", _external=True)]
    for service in content.get_services():
        urls.append(url_for("main.service_detail", service_id=service["id"], _external=True))
    for medicine in content.get_medicines():
        urls.append(url_for("medicines.detail", medicine_id=medicine["id"], _external=True))

    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"<url><loc>{u}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


def request_root():
    from flask import request

    return request.url_root


@main_bp.route("/")
def home():
    return render_template(
        "index.html",
        hero=content.get_hero(),
        about=content.get_about(),
        vision=content.get_vision(),
        why_choose_us=content.get_why_choose_us(),
        services=content.get_services(),
        doctor=content.get_doctor(),
        testimonials=content.get_testimonials(),
        gallery=content.get_gallery(),
        contact=content.get_contact(),
        nav_links=content.get_nav_links(),
    )


@main_bp.route("/service/<service_id>")
def service_detail(service_id):
    services = content.get_services()
    service = next((s for s in services if s.get("id") == service_id), None)
    return render_template("service_detail.html", service=service, services=services)
