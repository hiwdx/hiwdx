#!/usr/bin/env python3
"""Validate static SEO metadata; use --write-sitemap after adding a page."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://hiwd.com/'
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.meta = {}
        self.canonicals = []
        self.icons = []
        self.links = []
        self.title = ''
        self.lang = ''
        self.in_title = False
        self.in_json = False
        self.json_text = ''
        self.structured_data = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = attrs.get('lang', '')
        if tag == 'meta':
            key = attrs.get('name', attrs.get('property', attrs.get('http-equiv', ''))).lower()
            self.meta.setdefault(key, []).append(attrs.get('content', ''))
        if tag == 'link':
            if 'canonical' in attrs.get('rel', '').split():
                self.canonicals.append(attrs.get('href', ''))
            if 'icon' in attrs.get('rel', '').split():
                self.icons.append(attrs.get('href', ''))
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'title':
            self.in_title = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json = True
            self.json_text = ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_json:
            self.structured_data.append(json.loads(self.json_text))
            self.in_json = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_json:
            self.json_text += data

    def value(self, key):
        return self.meta.get(key, [''])[0]

    @property
    def indexable(self):
        directives = (self.value('robots') + ',' + self.value('googlebot')).lower()
        return bool(self.title) and 'refresh' not in self.meta and not any(token.strip() in ('noindex', 'none') for token in directives.split(','))


def url_for(path):
    relative = path.relative_to(ROOT).as_posix()
    return ORIGIN if relative == 'index.html' else urljoin(ORIGIN, relative)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-sitemap', action='store_true')
    args = parser.parse_args()
    paths = sorted(p for p in ROOT.rglob('*.html') if not any(part.startswith('.') for part in p.relative_to(ROOT).parts))
    pages = [Page(path) for path in paths]
    public = {url_for(page.path): page for page in pages if page.indexable}
    errors = []
    robots = RobotFileParser()
    robots.parse((ROOT / 'robots.txt').read_text().splitlines())
    if ORIGIN + 'sitemap.xml' not in (robots.site_maps() or []):
        errors.append('robots.txt must declare the canonical sitemap')
    for url, page in public.items():
        label = page.path.relative_to(ROOT)
        if page.canonicals != [url]:
            errors.append(f'{label}: expected one self-referencing canonical {url}')
        for key in ('description', 'og:title', 'og:description', 'og:url', 'og:site_name'):
            if len(page.meta.get(key, [])) != 1 or not page.value(key).strip():
                errors.append(f'{label}: missing, empty or duplicate {key}')
        if page.value('og:url') != url or page.value('og:site_name') != 'hiwd':
            errors.append(f'{label}: incorrect Open Graph URL or site name')
        if not page.lang or 'hiwd' not in page.title.lower():
            errors.append(f'{label}: missing language or title brand')
        if not page.icons or any(not (ROOT / unquote(urlsplit(icon).path).lstrip('/')).is_file() for icon in page.icons):
            errors.append(f'{label}: missing favicon asset')
        for agent in ('Googlebot', 'Bingbot'):
            if not robots.can_fetch(agent, url):
                errors.append(f'{label}: robots.txt blocks {agent}')
        for token in ('noindex', 'none', 'nosnippet'):
            if token in page.value('googlebot').lower() or token in page.value('robots').lower():
                errors.append(f'{label}: restrictive search directive {token}')

    for title, count in Counter(page.title for page in public.values()).items():
        if count > 1:
            errors.append(f'duplicate title: {title}')
    graph = public[ORIGIN].structured_data
    if not any(node.get('@type') == 'WebSite' and node.get('name') == 'hiwd' and node.get('url') == ORIGIN for doc in graph for node in doc.get('@graph', [])):
        errors.append('homepage must identify hiwd with WebSite structured data')
    error_page = next(page for page in pages if page.path.name == '404.html')
    if error_page.indexable:
        errors.append('404.html must remain noindex')

    # Ensure every public page is discoverable through real HTML links.
    seen, pending = set(), [ORIGIN]
    while pending:
        url = pending.pop()
        if url in seen or url not in public:
            continue
        seen.add(url)
        pending.extend(urljoin(url, link).split('#')[0] for link in public[url].links)
    for url in sorted(set(public) - seen):
        errors.append(f'page not linked from homepage: {url}')

    ET.register_namespace('', NS)
    sitemap = ET.Element(f'{{{NS}}}urlset')
    for url in sorted(public, key=lambda url: (url != ORIGIN, url)):
        ET.SubElement(ET.SubElement(sitemap, f'{{{NS}}}url'), f'{{{NS}}}loc').text = url
    # Omit optional lastmod rather than inventing content modification dates.
    ET.indent(sitemap, space='  ')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(sitemap, encoding='unicode') + '\n'
    sitemap_path = ROOT / 'sitemap.xml'
    if args.write_sitemap and not errors:
        sitemap_path.write_text(xml, encoding='utf-8')
    if not sitemap_path.is_file() or sitemap_path.read_text(encoding='utf-8') != xml:
        errors.append('sitemap.xml is stale; run python3 scripts/seo.py --write-sitemap')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'OK: {len(public)} indexable pages; metadata, canonicals, robots, JSON-LD, favicon, internal discovery and sitemap validated.')


if __name__ == '__main__':
    main()
