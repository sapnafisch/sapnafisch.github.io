#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "feedparser",
#     "requests",
#     "beautifulsoup4",
# ]
# ///
"""
substack_to_site.py
───────────────────
Fetches posts from your Atoms and Axioms Substack and converts them
into blog post HTML files for your GitHub Pages site (sapnafisch.github.io).

Usage:
    python substack_to_site.py

The script will:
1. Fetch your Substack RSS feed
2. Show you a list of recent posts
3. Let you pick which one to import
4. Let you choose which Field Notes category it belongs to
5. Generate a properly formatted HTML file ready for your site

Requirements:
    pip install feedparser requests beautifulsoup4
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import re
import sys
import os
import html
import textwrap


# ─── Configuration ───────────────────────────────────────────────────────────

SUBSTACK_FEED_URL = "https://atomsandaxioms.substack.com/feed"

# Your Field Notes blog categories
CATEGORIES = {
    "1": ("In Attendance",   "in-attendance"),
    "2": ("First Principles","first-principles"),
    "3": ("Inquiry",         "inquiry"),
    "4": ("At the Interface","at-the-interface"),
    "5": ("Marginalia",      "marginalia"),
    "6": ("Reflections",     "reflections"),
}

# Output directory — change this to your local repo path
# e.g., "/Users/sapna/sapnafisch.github.io/blog/posts/"
OUTPUT_DIR = os.environ.get("SITE_BLOG_DIR", "./output")


# ─── Fetch & Parse ───────────────────────────────────────────────────────────

def fetch_posts():
    """Fetch recent posts from Substack RSS feed."""
    print("\n📡  Fetching posts from Atoms and Axioms...")
    feed = feedparser.parse(SUBSTACK_FEED_URL)

    if feed.bozo and not feed.entries:
        print("❌  Could not fetch the RSS feed. Check your internet connection.")
        sys.exit(1)

    posts = []
    for entry in feed.entries:
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6]).strftime("%B %d, %Y")

        posts.append({
            "title": entry.get("title", "Untitled"),
            "link": entry.get("link", ""),
            "published": published,
            "summary": entry.get("summary", ""),
            "content": entry.get("content", [{}])[0].get("value", "")
                       if entry.get("content") else entry.get("summary", ""),
            "author": entry.get("author", "Sapna Sinha"),
        })

    return posts


def clean_html_content(raw_html):
    """Clean Substack HTML into content suitable for the site."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove Substack-specific elements (subscribe buttons, footers, etc.)
    for tag in soup.find_all(["div", "p", "a", "section"]):
        text = tag.get_text(strip=True).lower()
        if any(phrase in text for phrase in [
            "subscribe", "thanks for reading",
            "share this post", "leave a comment",
            "get the app", "start writing",
        ]):
            # Only remove if it's a short CTA-like element
            if len(tag.get_text(strip=True)) < 200:
                tag.decompose()

    # Remove empty paragraphs
    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()

    # Convert Substack image URLs — keep them as-is (they're CDN-hosted)
    # but ensure they have reasonable styling
    for img in soup.find_all("img"):
        img["style"] = "max-width: 100%; height: auto; border-radius: 4px; margin: 1em 0;"
        # Remove srcset to simplify
        if img.get("srcset"):
            del img["srcset"]

    return str(soup)


def generate_blog_html(post, category_name, category_slug):
    """Generate an HTML blog post file matching the site's style."""

    # Create a URL-friendly filename
    slug = re.sub(r'[^a-z0-9]+', '-', post["title"].lower()).strip('-')
    filename = f"{slug}.html"

    content = clean_html_content(post["content"])

    blog_html = textwrap.dedent(f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(post["title"])} — Sapna Sinha</title>
        <meta name="description" content="{html.escape(post['title'])}">

        <!-- Fonts matching your site -->
        <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;600&display=swap" rel="stylesheet">

        <style>
            :root {{
                --maroon: #4a1220;
                --maroon-light: #6b2035;
                --cream: #faf5f0;
                --text: #2c2c2c;
                --text-light: #666;
                --accent: #4a1220;
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: Georgia, 'Times New Roman', serif;
                color: var(--text);
                background: var(--cream);
                line-height: 1.8;
            }}

            .post-header {{
                background: var(--maroon);
                color: white;
                padding: 3rem 2rem 2rem;
                text-align: center;
            }}

            .post-header h1 {{
                font-family: Georgia, serif;
                font-size: 2.2rem;
                font-weight: 400;
                max-width: 800px;
                margin: 0 auto 0.75rem;
                line-height: 1.3;
            }}

            .post-meta {{
                font-family: 'Caveat', cursive;
                font-size: 1.15rem;
                opacity: 0.85;
            }}

            .post-meta .category {{
                display: inline-block;
                border: 1px solid rgba(255,255,255,0.4);
                padding: 0.15em 0.6em;
                border-radius: 3px;
                margin-right: 0.5em;
                font-size: 1rem;
            }}

            .post-content {{
                max-width: 720px;
                margin: 0 auto;
                padding: 2.5rem 1.5rem 4rem;
            }}

            .post-content p {{
                margin-bottom: 1.25em;
                font-size: 1.05rem;
            }}

            .post-content strong {{
                color: var(--maroon);
                font-weight: 600;
            }}

            .post-content h2, .post-content h3 {{
                font-family: Georgia, serif;
                color: var(--maroon);
                margin: 2em 0 0.75em;
                font-weight: 400;
            }}

            .post-content h2 {{ font-size: 1.6rem; }}
            .post-content h3 {{ font-size: 1.3rem; }}

            .post-content a {{
                color: var(--maroon);
                text-decoration: underline;
                text-decoration-color: rgba(74, 18, 32, 0.3);
                text-underline-offset: 3px;
            }}

            .post-content a:hover {{
                text-decoration-color: var(--maroon);
            }}

            .post-content img {{
                max-width: 100%;
                height: auto;
                border-radius: 4px;
                margin: 1.5em 0;
            }}

            .post-content blockquote {{
                border-left: 3px solid var(--maroon);
                margin: 1.5em 0;
                padding: 0.5em 1.5em;
                font-style: italic;
                color: var(--text-light);
            }}

            .post-footer {{
                max-width: 720px;
                margin: 0 auto;
                padding: 1.5rem 1.5rem 3rem;
                border-top: 1px solid rgba(74, 18, 32, 0.15);
                font-family: 'Caveat', cursive;
                font-size: 1.05rem;
                color: var(--text-light);
            }}

            .post-footer a {{
                color: var(--maroon);
            }}

            .back-link {{
                display: inline-block;
                margin-bottom: 1em;
                font-family: 'Caveat', cursive;
                font-size: 1.1rem;
            }}

            /* Responsive */
            @media (max-width: 600px) {{
                .post-header h1 {{ font-size: 1.6rem; }}
                .post-content {{ padding: 1.5rem 1rem 3rem; }}
            }}
        </style>
    </head>
    <body>

        <!-- Update this link to match your site's navigation -->
        <div style="padding: 1rem 1.5rem;">
            <a href="/blog.html" class="back-link" style="color: var(--maroon);">← Back to Field Notes</a>
        </div>

        <header class="post-header">
            <h1>{html.escape(post["title"])}</h1>
            <div class="post-meta">
                <span class="category">{html.escape(category_name)}</span>
                {html.escape(post["published"])}
            </div>
        </header>

        <article class="post-content">
            {content}
        </article>

        <footer class="post-footer">
            Originally published on
            <a href="{html.escape(post['link'])}" target="_blank" rel="noopener">Atoms and Axioms</a>
            · Sapna Sinha
        </footer>

    </body>
    </html>
    """)

    return filename, blog_html


# ─── Interactive CLI ─────────────────────────────────────────────────────────

def main():
    posts = fetch_posts()

    if not posts:
        print("No posts found in the feed.")
        sys.exit(1)

    # Show available posts
    print(f"\n{'─' * 60}")
    print(f"  Found {len(posts)} post(s) on Atoms and Axioms")
    print(f"{'─' * 60}\n")

    for i, post in enumerate(posts, 1):
        print(f"  [{i}]  {post['title']}")
        print(f"       {post['published']}  ·  {post['link'][:60]}...")
        print()

    # Pick a post
    while True:
        choice = input("  Which post to import? Enter number: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(posts):
                break
        except ValueError:
            pass
        print("  Invalid choice, try again.")

    selected = posts[idx]
    print(f"\n  ✓ Selected: {selected['title']}\n")

    # Pick a category
    print(f"{'─' * 60}")
    print("  Which Field Notes category?\n")
    for key, (name, _) in CATEGORIES.items():
        print(f"  [{key}]  {name}")
    print()

    while True:
        cat_choice = input("  Category number: ").strip()
        if cat_choice in CATEGORIES:
            break
        print("  Invalid choice, try again.")

    cat_name, cat_slug = CATEGORIES[cat_choice]
    print(f"\n  ✓ Category: {cat_name}\n")

    # Generate the file
    filename, blog_html = generate_blog_html(selected, cat_name, cat_slug)

    # Ensure output directory exists
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / filename
    out_path.write_text(blog_html, encoding="utf-8")

    print(f"{'─' * 60}")
    print(f"  ✅  Blog post created!")
    print(f"  📄  {out_path.resolve()}")
    print(f"  📂  Category: {cat_name}")
    print(f"  🔗  Original: {selected['link']}")
    print(f"{'─' * 60}")
    print()
    print("  Next steps:")
    print(f"  1. Move {filename} into your site's blog directory")
    print(f"  2. Add the post entry to your blog index page under '{cat_name}'")
    print("  3. git add, commit, push — and it's live!")
    print()


if __name__ == "__main__":
    main()