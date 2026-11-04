"""
Sync talks, writing (blog) and trainings from the kuanhoong.com repo into this
GitHub Pages site.

kuanhoong.com keeps its content as JSON in data/. This script reads those files
and updates the hand-written HTML here:

  talks.html      adds any talk that is not on this site yet (existing cards are left alone)
  blog.html       adds any Medium post that is not on this site yet
  index.html      rebuilds the "Recent Posts" table from the 5 newest posts
  trainings.html  rebuilds the training list from trainings.json
  assets/images/  copies the images used by newly added talks and trainings

Usage:
  python3 scripts/sync_from_kuanhoong_com.py /path/to/kuanhoong.com [--dry-run]
"""

import html
import json
import os
import re
import shutil
import sys

SRC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else '../kuanhoong.com'
DRY = '--dry-run' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
LINK_STYLE = 'font-size:0.8rem; color:var(--accent); text-decoration:none; display:inline-flex; align-items:center;'
SLIDES_ICON = '<img src="https://ssl.gstatic.com/docs/presentations/images/favicon5.ico" style="width:14px;height:14px;vertical-align:middle;margin-right:0.25rem;" alt="">'

changes = []


def esc(s):
    return html.escape(str(s or ''), quote=True)


def norm(s):
    return re.sub(r'\W+', '', html.unescape(str(s or '')).lower())


def load(name):
    with open(os.path.join(SRC, 'data', name), encoding='utf-8') as f:
        return json.load(f)


def read(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


def write(name, content):
    if DRY:
        return
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f:
        f.write(content)


def copy_image(src_path):
    """Map /images/foo.webp in kuanhoong.com to assets/images/foo.webp here."""
    if not src_path:
        return ''
    rel = src_path.lstrip('/')
    if rel.startswith('images/'):
        rel = rel[len('images/'):]
    dest_rel = 'assets/images/' + rel
    src_file = os.path.join(SRC, 'public', 'images', rel)
    dest_file = os.path.join(ROOT, dest_rel)
    if os.path.exists(src_file) and not os.path.exists(dest_file):
        if not DRY:
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)
        changes.append(f'image: {dest_rel}')
    return dest_rel if os.path.exists(src_file) or os.path.exists(dest_file) else ''


def link_html(link):
    kind = link.get('kind', 'link')
    label = link.get('label') or 'Link'
    if kind == 'slides':
        icon = SLIDES_ICON
    elif kind == 'video':
        icon = '<i class="fa-brands fa-youtube" style="margin-right:0.25rem;"></i>'
        label = 'Watch Video' if label == 'Video' else label
    elif kind == 'code':
        icon = '<i class="fa-solid fa-code" style="margin-right:0.25rem;"></i>'
    else:
        icon = '<i class="fa-solid fa-arrow-up-right-from-square" style="margin-right:0.25rem;"></i>'
    return (f'<a href="{esc(link["url"])}" target="_blank" rel="noopener" '
            f'style="{LINK_STYLE}">{icon}{esc(label)}</a>')


# ─────────────────────────────────────────────────────────────────────────────
# TALKS
# ─────────────────────────────────────────────────────────────────────────────
def talk_card(t):
    loc_icon = 'fa-globe' if t.get('online') else 'fa-location-dot'
    meta = []
    if t.get('location'):
        meta.append(f'<span class="talk-location"><i class="fa-solid {loc_icon}"></i> {esc(t["location"])}</span>')
    if t.get('attendees'):
        meta.append(f'<span class="attendee-badge"><i class="fa-solid fa-users"></i> {esc(t["attendees"])} attendees</span>')
    elif t.get('trained'):
        meta.append(f'<span class="attendee-badge"><i class="fa-solid fa-chalkboard-user"></i> {esc(t["trained"])} trained</span>')

    lines = [
        f'          <div class="talk-card" data-category="{esc(" ".join(t.get("categories") or ["ai"]))}">',
        f'            <div class="talk-date-col"><div class="talk-year">{t["year"]}</div><div class="talk-month">{esc(t.get("month", ""))}</div></div>',
        '            <div class="talk-content">',
        f'              <h3>{esc(t["title"])}</h3>',
        f'              <div class="talk-event">{esc(t.get("event", ""))}</div>',
        '              <div class="talk-meta">',
        *[f'                {m}' for m in meta],
        '              </div>',
    ]
    img = copy_image(t.get('image'))
    if img:
        alt = t.get('image_alt') or f'{t.get("event", "")}'
        lines.append(f'              <img class="talk-image" src="{esc(img)}" alt="{esc(alt)}" loading="lazy" decoding="async" />')
    if t.get('description'):
        lines += [
            '              <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem; line-height:1.6;">',
            f'                {esc(t["description"])}',
            '              </p>',
        ]
    if t.get('tags'):
        lines.append('              <div class="talk-tags">')
        lines += [f'                <span class="tag-pill">{esc(tag)}</span>' for tag in t['tags']]
        lines.append('              </div>')
    if t.get('links'):
        lines.append('              <div style="margin-top:0.6rem;">')
        lines += [f'                {link_html(l)}' for l in t['links']]
        lines.append('              </div>')
    lines += ['            </div>', '          </div>']
    return '\n'.join(lines)


def sync_talks():
    content = read('talks.html')
    src = load('talks.json')

    def existing_cards(c):
        out = []
        for m in re.finditer(r'<div class="talk-card"', c):
            chunk = c[m.start():m.start() + 4000]
            y = re.search(r'talk-year">(\d*)', chunk).group(1)
            mo = re.search(r'talk-month">(\w*)', chunk).group(1)
            ti = re.search(r'<h3>(.*?)</h3>', chunk, re.S).group(1)
            ev = re.search(r'talk-event">(.*?)</div>', chunk, re.S).group(1)
            out.append(dict(pos=m.start(), key=(y, mo, norm(ti)), event=norm(ev)))
        return out

    # Decide which source talks already exist. Same year+month+title can occur
    # more than once (same talk at different events), so match on counts and
    # prefer the card whose event text matches.
    cards = existing_cards(content)
    pool = {}
    for c in cards:
        pool.setdefault(c['key'], []).append(c)
    present = []
    for t in src:
        key = (str(t['year']), t.get('month', ''), norm(t['title']))
        cands = pool.get(key, [])
        if not cands:
            present.append(False)
            continue
        ev = norm(t.get('event'))
        best = next((c for c in cands if c['event'] == ev or ev in c['event'] or c['event'] in ev), cands[0])
        cands.remove(best)
        present.append(True)

    missing = [i for i, p in enumerate(present) if not p]
    for i in missing:
        t = src[i]
        card = talk_card(t)
        cards = existing_cards(content)
        # Anchor: the next talk (in source order, newest first) that is on the page.
        anchor_pos = None
        for j in range(i + 1, len(src)):
            if present[j]:
                k = (str(src[j]['year']), src[j].get('month', ''), norm(src[j]['title']))
                hit = next((c for c in cards if c['key'] == k), None)
                if hit:
                    anchor_pos, anchor_year = hit['pos'], k[0]
                    break
        year = str(t['year'])
        year_marker = f'<!-- {year} '
        if anchor_pos is not None and anchor_year == year:
            content = content[:anchor_pos] + card + '\n\n          ' + content[anchor_pos:]
        elif year_marker in content:
            # Year section exists but no later card in it: append at the end of the section.
            start = content.find(year_marker)
            nxt = re.search(r'<!-- \d{4} ', content[start + 10:])
            end = start + 10 + nxt.start() if nxt else content.find('</div>', content.rfind('<div class="talk-card"'))
            content = content[:end] + card + '\n\n          ' + content[end:]
        else:
            # New year section, placed before the newest older year.
            older = [y for y in range(int(year) - 1, 2000, -1) if f'<!-- {y} ' in content]
            section = f'<!-- {year} ─────────────────────────────────────────── -->\n\n{card}\n\n          '
            pos = content.find(f'<!-- {older[0]} ') if older else content.find('<div class="talks-list">') + len('<div class="talks-list">\n\n          ')
            content = content[:pos] + section + content[pos:]
        present[i] = True
        changes.append(f'talk: {t["year"]} {t.get("month", "")} {t["title"]} ({t.get("event", "")})')

    if missing:
        write('talks.html', content)


# ─────────────────────────────────────────────────────────────────────────────
# BLOG
# ─────────────────────────────────────────────────────────────────────────────
CAT_SLUG = {'Generative AI': 'genai', 'Machine Learning': 'ml', 'Tutorial': 'tutorial', 'Analytics': 'analytics'}


def date_key(d):
    parts = str(d).split()
    if len(parts) == 2 and parts[0] in MONTHS:
        return int(parts[1]) * 100 + MONTHS.index(parts[0]) + 1
    return 0


def sync_blog():
    content = read('blog.html')
    posts = sorted(load('blog.json'), key=lambda b: date_key(b['date']), reverse=True)
    have = {norm(re.sub(r'<[^>]+>', '', m)) for m in re.findall(r'<div class="blog-card".*?<h3>(.*?)</h3>', content, re.S)}

    # Fix cards that point at the generic Medium profile instead of the post itself.
    for b in posts:
        if re.fullmatch(r'https://medium\.com/@kuanhoong/?', b['url']):
            continue
        pat = re.compile(r'(<h3><a href=")https://medium\.com/@kuanhoong/?("[^>]*>\s*' + re.escape(esc(b['title'])) + r'\s*<)')
        if pat.search(content):
            content = pat.sub(lambda m: m.group(1) + esc(b['url']) + m.group(2), content, count=1)
            changes.append(f'blog: fixed link for {b["title"]}')

    have |= {u for u in re.findall(r'href="(https://[^"]*medium\.com[^"]*)"', content)}

    new = [b for b in posts if norm(b['title']) not in have and b['url'] not in have]
    for b in reversed(new):  # insert oldest first so the newest ends up on top
        slug = CAT_SLUG.get(b.get('category'), 'genai')
        card = f'''
          <!-- {esc(b["title"][:60])} -->
          <div class="blog-card" data-category="{slug}">
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <span class="blog-date">{esc(b["date"])}</span>
                <span class="blog-category">{esc(b.get("category", "Generative AI"))}</span>
              </div>
              <h3><a href="{esc(b["url"])}" target="_blank" rel="noopener">
                {esc(b["title"])}
                <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:0.65rem; margin-left:0.3rem;"></i>
              </a></h3>
              <p>{esc(b.get("summary", ""))}</p>
            </div>
          </div>
'''
        anchor = '<div class="blog-grid">\n'
        pos = content.find(anchor) + len(anchor)
        content = content[:pos] + card + content[pos:]
        changes.append(f'blog: {b["date"]} {b["title"]}')
    if new or any(c.startswith('blog: fixed') for c in changes):
        write('blog.html', content)

    # Homepage "Recent Posts": always the 5 newest.
    index = read('index.html')
    rows = []
    for b in posts[:5]:
        rows.append(f'''            <tr>
              <td class="post-date">{esc(b["date"])}</td>
              <td class="post-title">
                <a href="{esc(b["url"])}" target="_blank" rel="noopener">{esc(b["title"])}</a>
                <span class="badge post-tag">{esc(b.get("category", ""))}</span>
              </td>
            </tr>''')
    new_index = re.sub(r'(<table class="posts-table">\s*<tbody>\n).*?(\s*</tbody>)',
                       lambda m: m.group(1) + '\n'.join(rows) + m.group(2), index, count=1, flags=re.S)
    if new_index != index:
        write('index.html', new_index)
        changes.append('index: refreshed Recent Posts')


# ─────────────────────────────────────────────────────────────────────────────
# TRAININGS
# ─────────────────────────────────────────────────────────────────────────────
TRACK_FILTER = {'AI / ML': 'ai', 'Python': 'python', 'R Programming': 'r', 'Data Analytics': 'data', 'Machine Learning': 'ai'}
ICON_KEYWORDS = [
    ('engineering', 'fa-solid fa-microchip'), ('power query', 'fa-solid fa-table'),
    ('tidy statistics', 'fa-solid fa-chart-column'), ('data analytics with r', 'fa-solid fa-magnifying-glass-chart'),
    ('python', 'fa-brands fa-python'), ('artificial intelligence', 'fa-solid fa-robot'),
    ('industry revolution', 'fa-solid fa-industry'), ('machine learning with r', 'fa-solid fa-brain'),
    ('big data', 'fa-solid fa-database'), ('introduction to r', 'fa-solid fa-code'),
]


def training_icon(title):
    t = title.lower()
    for kw, icon in ICON_KEYWORDS:
        if kw in t:
            return icon
    return 'fa-solid fa-chalkboard-user'


def training_card(t):
    tracks = t.get('tracks') or []
    cat = TRACK_FILTER.get(tracks[0], 'ai') if tracks else 'ai'
    lines = [
        f'          <div class="training-card" data-category="{cat}">',
        f'            <div class="training-icon"><i class="{training_icon(t["title"])}"></i></div>',
        '            <div class="training-content">',
        f'              <h3>{esc(t["title"])}</h3>',
        '              <div class="training-meta">',
        f'                <span class="training-duration"><i class="fa-regular fa-clock"></i> {esc(t.get("duration", ""))}</span>',
        *[f'                <span class="badge">{esc(tr)}</span>' for tr in tracks],
        '              </div>',
        f'              <p>{esc(t.get("description", ""))}</p>',
    ]
    img = copy_image(t.get('image'))
    if img:
        lines.append(f'              <img class="talk-image" src="{esc(img)}" alt="{esc(t.get("image_alt") or t["title"])}" loading="lazy" decoding="async" />')
    deliveries = t.get('deliveries') or []
    if deliveries:
        lines.append('              <div style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem; line-height:1.6;">')
        lines.append('                <div style="font-weight:600; margin-bottom:0.2rem;">Recently delivered</div>')
        for d in deliveries:
            bits = [esc(d.get('venue', ''))]
            if d.get('dates'):
                bits.append(esc(d['dates']))
            if d.get('participants'):
                bits.append(f'{esc(d["participants"])} participants')
            if d.get('rating'):
                bits.append(f'rated {esc(d["rating"])}')
            lines.append(f'                <div><i class="fa-solid fa-location-dot"></i> {" &middot; ".join(bits)}</div>')
            if d.get('feedback'):
                lines.append(f'                <div style="font-style:italic; margin:0.15rem 0 0.35rem 1.1rem;">Feedback: {esc(d["feedback"])}</div>')
        lines.append('              </div>')
    elif t.get('recently_delivered'):
        lines.append(f'              <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem;"><i class="fa-solid fa-location-dot"></i> Recently delivered: {esc(t["recently_delivered"])}</p>')
    if t.get('links'):
        lines.append('              <div style="margin-top:0.6rem;">')
        lines += [f'                {link_html(dict(l, kind=l.get("kind", "slides")))}' for l in t['links']]
        lines.append('              </div>')
    lines += ['            </div>', '          </div>']
    return '\n'.join(lines)


def sync_trainings():
    content = read('trainings.html')
    cards = '\n' + '\n\n'.join(training_card(t) for t in load('trainings.json')) + '\n'
    new = re.sub(r'(<div class="trainings-list">\n).*?(\n        </div>\n      </div><!-- /filter-group -->)',
                 lambda m: m.group(1) + cards + m.group(2), content, count=1, flags=re.S)
    if new == content:
        return
    if '<div class="trainings-list">' not in new:
        raise SystemExit('trainings.html: could not find the training list')
    write('trainings.html', new)
    changes.append('trainings: rebuilt list from trainings.json')


if __name__ == '__main__':
    sync_talks()
    sync_blog()
    sync_trainings()
    print(('[dry run] ' if DRY else '') + (f'{len(changes)} change(s):' if changes else 'Already up to date.'))
    for c in changes:
        print('  -', c)
