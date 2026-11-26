#!/usr/bin/env python3
"""Build one preview website and one outreach email draft per business.

Reads  data/businesses.json and config.json
Writes sites/<slug>/index.html, sites/index.html (gallery),
       emails/<slug>.txt and emails/outreach.csv
"""
import csv
import datetime
import html
import json
import pathlib
import re
import sys
import unicodedata
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "templates" / "site.html").read_text()

# Look and wording per business type. Anything not listed falls back to "default".
THEMES = {
    "restaurant": dict(label="Restaurant", accent="#c2410c", ink="#fff", font="Fraunces:wght@600;700", family="'Fraunces',serif",
                       services_title="What we serve", headline="Home-style food, made fresh every day"),
    "bakery":     dict(label="Bakery", accent="#b45309", ink="#fff", font="Fraunces:wght@600;700", family="'Fraunces',serif",
                       services_title="From our ovens", headline="Baked fresh, every morning"),
    "cafe":       dict(label="Café", accent="#7c4a2d", ink="#fff", font="Fraunces:wght@600;700", family="'Fraunces',serif",
                       services_title="On the menu", headline="Your neighborhood coffee stop"),
    "barber":     dict(label="Barbershop", accent="#1d4ed8", ink="#fff", font="Oswald:wght@500;600", family="'Oswald',sans-serif",
                       services_title="Cuts & services", headline="Sharp cuts. Easy chairs."),
    "salon":      dict(label="Salon", accent="#be185d", ink="#fff", font="Playfair+Display:wght@600;700", family="'Playfair Display',serif",
                       services_title="Our services", headline="Look good, feel better"),
    "nails":      dict(label="Nail Salon", accent="#db2777", ink="#fff", font="Playfair+Display:wght@600;700", family="'Playfair Display',serif",
                       services_title="Our services", headline="Clean, careful, beautiful nails"),
    "auto":       dict(label="Auto Repair", accent="#dc2626", ink="#fff", font="Oswald:wght@500;600", family="'Oswald',sans-serif",
                       services_title="What we fix", headline="Honest repairs, done right"),
    "cleaning":   dict(label="Cleaning Service", accent="#0e7490", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="What we clean", headline="A spotless space, without the stress"),
    "trades":     dict(label="Home Services", accent="#a16207", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="What we do", headline="Reliable work, fair prices"),
    "landscaping":dict(label="Landscaping", accent="#15803d", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="What we do", headline="Yards you'll be proud of"),
    "fitness":    dict(label="Fitness", accent="#ea580c", ink="#fff", font="Oswald:wght@500;600", family="'Oswald',sans-serif",
                       services_title="Classes & training", headline="Get stronger, together"),
    "retail":     dict(label="Shop", accent="#4338ca", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="What you'll find", headline="Come see what's new in store"),
    "tailor":     dict(label="Tailor & Alterations", accent="#6d28d9", ink="#fff", font="Playfair+Display:wght@600;700", family="'Playfair Display',serif",
                       services_title="Our services", headline="Clothes that fit you perfectly"),
    "pet":        dict(label="Pet Care", accent="#0f766e", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="Our services", headline="Happy pets, happy owners"),
    "default":    dict(label="Local Business", accent="#2563eb", ink="#fff", font="Manrope:wght@600;700", family="'Manrope',sans-serif",
                       services_title="What we offer", headline="Proudly serving our neighbors"),
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"['’]", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def tel(phone):
    return re.sub(r"[^0-9+]", "", phone or "")


def build_site(b, theme):
    phone, email = b.get("phone"), b.get("email")
    call = f'<a class="btn" href="tel:{tel(phone)}">Call {esc(phone)}</a>' if phone else ""
    mail = f'<a class="btn ghost" href="mailto:{esc(email)}">Email us</a>' if email else ""
    directions = (f'<a class="btn ghost" href="https://www.google.com/maps/dir/?api=1&destination='
                  f'{urllib.parse.quote(b["address"])}">Get directions</a>')
    hero_actions = call + (mail or directions)

    services = "".join(
        f'<div class="card"><h3>{esc(s["name"] if isinstance(s, dict) else s)}</h3>'
        + (f'<p>{esc(s.get("detail"))}</p>' if isinstance(s, dict) and s.get("detail") else "")
        + "</div>"
        for s in b.get("services", [])
    )

    facts = [("Type", theme["label"]), ("Location", f'{b["city"]}, {b["state"]}')]
    if b.get("rating"):
        facts.append(("Customer rating", b["rating"]))
    if b.get("since"):
        facts.append(("Serving since", b["since"]))
    if b.get("price"):
        facts.append(("Price range", b["price"]))
    facts_html = "".join(f"<li><span>{esc(k)}</span><span>{esc(v)}</span></li>" for k, v in facts)

    hours = b.get("hours") or {}
    hours_html = ""
    if hours:
        rows = "".join(f"<tr><td>{esc(d)}</td><td>{esc(h)}</td></tr>" for d, h in hours.items())
        hours_html = f"<p><strong>Hours</strong></p><table class='hours'>{rows}</table>"

    contact_lines = ""
    if phone:
        contact_lines += f'<p><strong>Phone</strong><br><a href="tel:{tel(phone)}">{esc(phone)}</a></p>'
    if email:
        contact_lines += f'<p><strong>Email</strong><br><a href="mailto:{esc(email)}">{esc(email)}</a></p>'

    about = b.get("about") or (
        f'{b["name"]} is a locally owned {theme["label"].lower()} in {b["city"]}, {b["state"]}. '
        "Stop by and say hello. We'd love to meet you."
    )
    tagline = b.get("tagline") or f'Locally owned {theme["label"].lower()} serving {b["city"]} and nearby neighborhoods.'

    values = {
        "name": esc(b["name"]),
        "category_label": esc(theme["label"]),
        "city": esc(b["city"]),
        "state": esc(b["state"]),
        "meta_description": esc(f'{b["name"]}: {tagline}'),
        "font_url": theme["font"],
        "font_family": theme["family"],
        "accent": theme["accent"],
        "accent_ink": theme["ink"],
        "header_cta": f'<a class="btn" href="tel:{tel(phone)}">Call</a>' if phone else "",
        "headline": esc(b.get("headline") or theme["headline"]),
        "tagline": esc(tagline),
        "hero_actions": hero_actions,
        "services_title": esc(theme["services_title"]),
        "services_html": services,
        "about": esc(about),
        "facts_html": facts_html,
        "hours_html": hours_html,
        "address": esc(b["address"]),
        "contact_lines": contact_lines,
        "map_query": urllib.parse.quote(f'{b["name"]}, {b["address"]}'),
        "year": str(datetime.date.today().year),
    }
    out = TEMPLATE
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", v)
    leftover = re.findall(r"{{\w+}}", out)
    if leftover:
        raise SystemExit(f"Unfilled placeholders for {b['name']}: {leftover}")
    return out


def plural(label):
    label = label.lower()
    if label.endswith("y"):
        return label[:-1] + "ies"
    if label.endswith("s"):
        return label + " businesses"
    return label + "s"


def build_email(b, theme, cfg, preview_url):
    sender = cfg["sender"]
    subject = f'I made a free website preview for {b["name"]}'
    greeting = f'Hi {b["owner"]},' if b.get("owner") else f'Hi {b["name"]} team,'
    body = f"""{greeting}

I came across {b["name"]} while looking at {plural(theme["label"])} in {b["city"]}{(" and saw " + b["hook"]) if b.get("hook") else ""}. I noticed you don't have a website yet, so I put together a free preview of what one could look like:

{preview_url}

It already has your {"menu" if theme["label"] in ("Restaurant","Café","Bakery") else "services"}{", hours" if b.get("hours") else ""}, phone number and a map, and it works on phones. Customers who search for you on Google could find all of this in one place.

If you like it, I can put it live on your own domain and make any changes you want, for {cfg["offer"]["price"]}. {cfg["offer"]["includes"]} If it's not for you, no problem at all. The preview is yours to keep either way.

Would you be open to a quick 10-minute call this week?

Thanks,
{sender["name"]}
{sender.get("title", "")}
{sender["email"]}{(chr(10) + sender["phone"]) if sender.get("phone") else ""}
{sender["postal_address"]}

If you'd rather not hear from me again, just reply "no thanks" and I won't contact you again.
"""
    return subject, body


def main():
    cfg = json.loads((ROOT / "config.json").read_text())
    data_file = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "businesses.json"
    businesses = json.loads(data_file.read_text())
    sites_dir, emails_dir = ROOT / "sites", ROOT / "emails"
    sites_dir.mkdir(exist_ok=True)
    emails_dir.mkdir(exist_ok=True)

    rows, cards = [], []
    for b in businesses:
        slug = b.get("slug") or slugify(f'{b["name"]}-{b["city"]}')
        theme = THEMES.get(b.get("category"), THEMES["default"])
        (sites_dir / slug).mkdir(exist_ok=True)
        (sites_dir / slug / "index.html").write_text(build_site(b, theme))

        preview_url = cfg["preview_base_url"].rstrip("/") + f"/{slug}/"
        subject, body = build_email(b, theme, cfg, preview_url)
        (emails_dir / f"{slug}.txt").write_text(f"To: {b.get('email') or '(no public email: send by contact form or phone)'}\nSubject: {subject}\n\n{body}")

        rows.append({
            "slug": slug, "name": b["name"], "category": theme["label"], "city": b["city"], "state": b["state"],
            "email": b.get("email", ""), "phone": b.get("phone", ""), "contact_channel": b.get("contact_channel", "email" if b.get("email") else "phone"),
            "preview_url": preview_url, "subject": subject, "source": b.get("source", ""), "notes": b.get("note", ""), "status": "draft",
        })
        cards.append(f'<a class="c" href="{slug}/index.html"><b>{esc(b["name"])}</b><span>{esc(theme["label"])} · {esc(b["city"])}, {esc(b["state"])}</span></a>')

    with open(emails_dir / "outreach.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    (sites_dir / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Website previews</title>
<style>:root{{--bg:#fbfaf8;--ink:#1c1b19;--muted:#5f5b55;--line:#e7e3dc;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141312;--ink:#f2efe9;--muted:#aaa49a;--line:#33302c;--card:#1d1c1a}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;padding:40px 16px}}
main{{max-width:1040px;margin:0 auto}}h1{{margin:0 0 8px}}p{{color:var(--muted);margin:0 0 28px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.c{{display:flex;flex-direction:column;gap:4px;padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--card);text-decoration:none;color:inherit}}
.c span{{color:var(--muted);font-size:.9rem}}.c:hover{{border-color:var(--ink)}}</style></head>
<body><main><h1>Website previews</h1><p>{len(cards)} one-page sites, one per business.</p>
<div class="g">{''.join(cards)}</div></main></body></html>""")
    print(f"Built {len(rows)} sites in sites/ and {len(rows)} email drafts in emails/")


if __name__ == "__main__":
    main()
