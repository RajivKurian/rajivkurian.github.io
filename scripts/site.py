#!/usr/bin/env python3
"""Build the independent article repository with its locked Quarto tools."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def environment():
    system = (platform.system(), platform.machine())
    platforms = {('Darwin', 'arm64'): 'osx-arm64',
                 ('Linux', 'x86_64'): 'linux-64'}
    if system not in platforms:
        raise RuntimeError(f'No environment lock for {system}')
    lock = ROOT / 'env' / (platforms[system] + '.lock')
    # Hash both the requested versions and exact artifacts. Including this script
    # also gives setup changes a fresh prefix instead of modifying an old env.
    digest = hashlib.sha256()
    for path in (ROOT / 'environment.yml', lock, Path(__file__).resolve()):
        digest.update(path.relative_to(ROOT).as_posix().encode() + b'\0')
        digest.update(path.read_bytes() + b'\0')
    identity = digest.hexdigest()
    prefix = ROOT / '.envs' / f'authoring-{platforms[system]}-{identity[:16]}'
    return prefix, lock, identity


def verify(prefix, lock, identity):
    marker = prefix / '.article-environment'
    if not marker.exists() or marker.read_text().strip() != identity:
        raise RuntimeError('Run python3 scripts/site.py setup first.')
    for executable in ('quarto', 'deno', 'pandoc', 'sass'):
        if not (prefix / 'bin' / executable).exists():
            raise RuntimeError(f'Missing tool {executable}; recreate this prefix.')
    expected = {line.strip() for line in lock.read_text().splitlines()
                if line.startswith('https://')}
    actual = set()
    for record in (prefix / 'conda-meta').glob('*.json'):
        package = json.loads(record.read_text())
        actual.add(package['url'] + '#' + package['sha256'])
    if actual != expected:
        raise RuntimeError('Environment packages differ from the lock; recreate this prefix.')


def setup(prefix, lock, identity):
    if (prefix / '.article-environment').exists():
        verify(prefix, lock, identity)
        print(f'Environment ready: {prefix}')
        return
    conda = os.environ.get('CONDA_EXE') or shutil.which('conda')
    if not conda:
        raise RuntimeError('Install conda or set CONDA_EXE to its executable.')
    subprocess.run([conda, 'create', '--yes', '--prefix', str(prefix),
                    '--override-channels', '-c', 'conda-forge',
                    '--file', str(lock)], check=True)
    (prefix / '.article-environment').write_text(identity + '\n')
    verify(prefix, lock, identity)
    print(f'Environment ready: {prefix}')


def run_quarto(prefix, args):
    env = os.environ.copy()
    env['PATH'] = str(prefix / 'bin') + os.pathsep + env.get('PATH', '')
    env['CONDA_PREFIX'] = str(prefix)
    # The conda package installs tools separately from Quarto. Resolve them from
    # this prefix, including deno_dom, whose activation hook embeds a build path.
    for name, executable in {'DENO': 'deno', 'PANDOC': 'pandoc',
                             'ESBUILD': 'esbuild', 'TYPST': 'typst',
                             'DART_SASS': 'sass'}.items():
        env['QUARTO_' + name] = str(prefix / 'bin' / executable)
    extension = 'dylib' if platform.system() == 'Darwin' else 'so'
    env['QUARTO_DENO_DOM'] = str(prefix / 'lib' / ('deno_dom.' + extension))
    env['QUARTO_SHARE_PATH'] = str(prefix / 'share' / 'quarto')
    env['QUARTO_CONDA_PREFIX'] = str(prefix)
    subprocess.run([str(prefix / 'bin' / 'quarto'), *args], cwd=ROOT,
                   env=env, check=True)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.resources = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        for key in ('src', 'poster', 'data'):
            if key in attrs:
                self.resources.append(attrs[key])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.resources.append(attrs.get('href', ''))


def check(directory):
    paths = list(directory.rglob('*.html'))
    if not paths:
        raise RuntimeError(f'No HTML found in {directory}; build first.')
    pages = {path.resolve(): Page(path) for path in paths}
    errors = []
    for path, page in pages.items():
        for resource in page.resources:
            if resource and not resource.startswith(('data:', '#')):
                errors.append(f'{path.name}: resource is not embedded: {resource}')
        for href in page.links:
            link = urlsplit(href)
            if link.scheme or link.netloc:
                continue
            target = (path.parent / unquote(link.path)).resolve() if link.path else path
            if target.is_dir():
                target /= 'index.html'
            if not target.exists():
                errors.append(f'{path.name}: missing link {href}')
            elif link.fragment and target in pages and unquote(link.fragment) not in pages[target].ids:
                errors.append(f'{path.name}: missing anchor {href}')
    if errors:
        raise RuntimeError('\n'.join(errors))
    print(f'Checked {len(paths)} HTML pages: links resolve and resources are embedded.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('setup', 'preview', 'build', 'check', 'fixture'))
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.command == 'check':
        check(ROOT / 'dist')
        return
    prefix, lock, identity = environment()
    if args.command == 'setup':
        setup(prefix, lock, identity)
        return
    verify(prefix, lock, identity)
    if args.command == 'preview':
        run_quarto(prefix, ['preview', '--no-browser', '--port', str(args.port)])
    elif args.command == 'fixture':
        run_quarto(prefix, ['render', '--profile', 'preview'])
        check(ROOT / '.preview')
    else:
        run_quarto(prefix, ['render'])
        check(ROOT / 'dist')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
