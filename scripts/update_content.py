"""
Auto-update site content from Google Form submissions.
Triggered by GitHub Actions repository_dispatch event.
"""

import json
import os
import re
import html as html_module

raw = os.environ.get('PAYLOAD', '{}')
payload = json.loads(raw)
content_type = payload.get('type', '').strip().lower()

print(f"Processing: {content_type}")
print(f"Payload: {json.dumps(payload, indent=2)}")


def esc(s):
    return html_module.escape(str(s)) if s else ''


# ─────────────────────────────────────────────────────────────────────────────
# TALK
# ─────────────────────────────────────────────────────────────────────────────
if content_type == 'talk':
    title     = payload.get('title', '').strip()
    event     = payload.get('event', '').strip()
    location  = payload.get('location', '').strip()
    month     = payload.get('month', '').strip()
    year      = payload.get('year', '').strip()
    category  = payload.get('category', 'ai').strip()
    talk_type = payload.get('talk_type', 'talk').strip()
    attendees = payload.get('attendees', '').strip()
    trained   = payload.get('trained', '').strip()
    desc      = payload.get('desc', '').strip()
    tags_raw  = payload.get('tags', '').strip()
    slides    = payload.get('slides', '').strip()
    video     = payload.get('video', '').strip()

    type_labels = {
        'talk': 'Public Speaking', 'workshop': 'Workshop',
        'webinar': 'Webinar', 'panel': 'Panel Discussion', 'judge': 'Judge'
    }
    type_label = type_labels.get(talk_type, 'Public Speaking')
    is_online  = any(x in location.lower() for x in ['online', 'virtual', 'remote'])
    loc_icon   = 'fa-globe' if is_online else 'fa-location-dot'

    # meta row
    meta_parts = []
    if location:
        meta_parts.append(f'<span class="talk-location"><i class="fa-solid {loc_icon}"></i> {esc(location)}</span>')
    if attendees:
        meta_parts.append(f'<span class="attendee-badge"><i class="fa-solid fa-users"></i> {esc(attendees)} attendees</span>')
    elif trained:
        meta_parts.append(f'<span class="attendee-badge"><i class="fa-solid fa-chalkboard-user"></i> {esc(trained)} trained</span>')
    meta_html = ('\n              ' + '\n              '.join(meta_parts) + '\n              ') if meta_parts else ''

    # tags
    tags_html = ''
    if tags_raw:
        tag_list  = [t.strip() for t in tags_raw.split(',') if t.strip()]
        pills     = '\n'.join(f'                <span class="tag-pill">{esc(t)}</span>' for t in tag_list)
        tags_html = f'\n              <div class="talk-tags">\n{pills}\n              </div>'

    # links
    links_parts = []
    if slides:
        links_parts.append(f'<a href="{esc(slides)}" target="_blank" rel="noopener" style="font-size:0.8rem; color:var(--accent); text-decoration:none; margin-right:1rem;"><i class="fa-solid fa-presentation-screen"></i> View Slides</a>')
    if video:
        links_parts.append(f'<a href="{esc(video)}" target="_blank" rel="noopener" style="font-size:0.8rem; color:var(--accent); text-decoration:none;"><i class="fa-brands fa-youtube"></i> Watch Video</a>')
    links_html = (f'\n              <div style="margin-top:0.6rem;">' + ''.join(links_parts) + '\n              </div>') if links_parts else ''

    desc_html = f'\n              <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem; line-height:1.6;">\n                {esc(desc)}\n              </p>' if desc else ''

    card = f'''          <div class="talk-card" data-category="{category}">
            <div class="talk-date-col"><div class="talk-year">{year}</div><div class="talk-month">{month}</div></div>
            <div class="talk-content">
              <h3>{esc(title)}</h3>
              <div class="talk-event">{esc(type_label)} · {esc(event)}</div>
              <div class="talk-meta">{meta_html}</div>{desc_html}{tags_html}{links_html}
            </div>
          </div>'''

    with open('talks.html', 'r', encoding='utf-8') as f:
        content = f.read()

    year_marker = f'<!-- {year}'
    if year_marker in content:
        # Insert before the first talk-card in this year's section
        year_pos  = content.find(year_marker)
        card_pos  = content.find('<div class="talk-card"', year_pos)
        if card_pos != -1:
            content = content[:card_pos] + card + '\n\n          ' + content[card_pos:]
        else:
            end_of_comment_line = content.find('\n', year_pos) + 1
            content = content[:end_of_comment_line] + '\n' + card + '\n\n' + content[end_of_comment_line:]
    else:
        # New year — insert section before the next lower year, or at top of talks-list
        inserted = False
        for y in range(int(year) - 1, 2015, -1):
            prev = f'<!-- {y}'
            if prev in content:
                pos = content.find(prev)
                section = f'          <!-- {year} ─────────────────────────────────────────── -->\n\n{card}\n\n          '
                content = content[:pos] + section + content[pos:]
                inserted = True
                break
        if not inserted:
            anchor = '<div class="talks-list">'
            pos    = content.find(anchor) + len(anchor) + 1
            section = f'\n          <!-- {year} ─────────────────────────────────────────── -->\n\n{card}\n\n'
            content = content[:pos] + section + content[pos:]

    with open('talks.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Added talk: {title}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOG POST
# ─────────────────────────────────────────────────────────────────────────────
elif content_type == 'blog':
    title     = payload.get('title', '').strip()
    url       = payload.get('url', '').strip()
    month     = payload.get('month', '').strip()
    year      = payload.get('year', '').strip()
    category  = payload.get('category', 'genai').strip()
    cat_labels = {'genai': 'Generative AI', 'ml': 'Machine Learning', 'tutorial': 'Tutorial', 'analytics': 'Analytics'}
    cat_label = payload.get('cat_label', '').strip() or cat_labels.get(category, 'Generative AI')
    desc      = payload.get('desc', '').strip()

    # blog.html card
    card = f'''
          <div class="blog-card" data-category="{category}">
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <span class="blog-date">{month} {year}</span>
                <span class="blog-category">{esc(cat_label)}</span>
              </div>
              <h3><a href="{esc(url)}" target="_blank" rel="noopener">
                {esc(title)}
                <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:0.65rem; margin-left:0.3rem;"></i>
              </a></h3>
              <p>{esc(desc)}</p>
            </div>
          </div>
'''

    with open('blog.html', 'r', encoding='utf-8') as f:
        content = f.read()

    anchor = '<div class="blog-grid">'
    pos    = content.find(anchor) + len(anchor)
    content = content[:pos] + card + content[pos:]

    with open('blog.html', 'w', encoding='utf-8') as f:
        f.write(content)

    # index.html — add row, keep only 5 rows in tbody
    index_row = f'''              <tr>
                <td class="post-date">{month} {year}</td>
                <td class="post-title">
                  <a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>
                  <span class="badge post-tag">{esc(cat_label)}</span>
                </td>
              </tr>'''

    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the tbody in recent posts section
    tbody_pos = content.find('<tbody>')
    if tbody_pos != -1:
        insert_pos = content.find('\n', tbody_pos) + 1
        content = content[:insert_pos] + index_row + '\n' + content[insert_pos:]

        # Trim to max 5 rows: find all <tr>...</tr> blocks after tbody
        tbody_start = content.find('<tbody>')
        tbody_end   = content.find('</tbody>', tbody_start)
        tbody_inner = content[tbody_start:tbody_end]
        rows        = re.findall(r'(<tr>.*?</tr>)', tbody_inner, re.DOTALL)
        if len(rows) > 5:
            # Remove excess rows from end
            for extra_row in rows[5:]:
                # Remove row and surrounding whitespace
                content = re.sub(r'\s*' + re.escape(extra_row), '', content, count=1)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Added blog post: {title}")


# ─────────────────────────────────────────────────────────────────────────────
# UNKNOWN TYPE
# ─────────────────────────────────────────────────────────────────────────────
else:
    print(f"❌ Unknown content type: '{content_type}'. Expected 'talk' or 'blog'.")
    exit(1)
