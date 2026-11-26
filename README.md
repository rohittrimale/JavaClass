# Local business website previews

Finds small businesses that don't have a website, builds a free one-page preview site for each, and drafts a short outreach email offering to put it live.

## How it works

1. **Leads** go in `data/businesses.json`, one record per business (see `data/example.json` for every field).
   Only add a business after checking that it really has no website (Google Maps, Yelp, a web search for its name).
2. **Your details** go in `config.json`: your name, email, mailing address, price, and where the previews will be hosted.
3. **Generate** everything:

   ```sh
   python3 scripts/generate.py                     # uses data/businesses.json
   python3 scripts/generate.py data/example.json   # try it with the sample
   ```

   This writes:
   - `sites/<slug>/index.html`: one responsive page per business (services, about, hours, phone, map), themed by category
   - `sites/index.html`: a gallery linking all previews
   - `emails/<slug>.txt`: a personal email draft for each business
   - `emails/outreach.csv`: a tracker with contact, preview link, subject and status

4. **Host** the `sites/` folder anywhere static (GitHub Pages, Netlify, Cloudflare Pages) and set `preview_base_url` to match.
5. **Review and send** the emails yourself. Nothing is sent automatically.

## Lead record fields

| Field | Required | Notes |
|---|---|---|
| `name`, `city`, `state`, `address` | yes | |
| `category` | no | `restaurant`, `bakery`, `cafe`, `barber`, `salon`, `nails`, `auto`, `cleaning`, `trades`, `landscaping`, `fitness`, `retail`, `tailor`, `pet`; anything else uses a neutral theme |
| `phone`, `email` | no | at least one is needed to reach them |
| `services` | no | list of names, or `{name, detail}` objects |
| `hours` | no | `{ "Mon–Fri": "9am – 7pm" }` |
| `owner`, `hook` | no | personalize the email greeting and opening line |
| `rating`, `since`, `price`, `about`, `tagline`, `headline` | no | page copy overrides |
| `source` | no | where you found the business, for your own records |

## Sending responsibly

Each preview carries a banner saying it was made for the business and isn't published by them. Each email includes your mailing address and an opt-out line, which US law (CAN-SPAM) requires for commercial email. Honor every "no thanks".
