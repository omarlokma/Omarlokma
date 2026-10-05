import json, os, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

USER = "Omarlokma"
ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "assets" / "omar.jpg"
OUT = ROOT / "profile.svg"

def gh(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept":"application/vnd.github+json","User-Agent":USER}
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

u = gh(f"/users/{USER}")
repos = gh(f"/users/{USER}/repos?per_page=100&sort=updated")
public_repos = u.get("public_repos", len(repos))
followers = u.get("followers", 0)
stars = sum(r.get("stargazers_count", 0) for r in repos)

# Get the full all-time commit contribution count from GitHub's
# ContributionsCollection. GitHub exposes this through GraphQL and limits a
# contribution collection query to a date range, so we sum one year at a time.
from datetime import date

def gql(query, variables):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": USER,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.load(r)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result["data"]

query = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
    }
  }
}
"""

# Use the account creation year as the lower bound and the current year as
# the upper bound. This produces an all-time contribution total.
created_year = int(user_created_year := u.get("created_at", "2015")[:4])
current_year = date.today().year
commits = 0

for year in range(created_year, current_year + 1):
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    try:
        data = gql(query, {"login": USER, "from": start, "to": end})
        commits += data["user"]["contributionsCollection"]["totalCommitContributions"]
    except Exception as exc:
        print(f"Warning: could not read contributions for {year}: {exc}")

gray = Image.open(IMG).convert("L")
w,h = gray.size
crop = gray.crop((int(w*.08),int(h*.08),int(w*.92),int(h*.92)))
small = ImageOps.autocontrast(crop.resize((42,max(22,int(crop.height/crop.width*42*.50))),Image.Resampling.LANCZOS))
chars="@%#*+=-:. "
ascii_lines=[]
for y in range(small.height):
    ascii_lines.append("".join(chars[min(9,int(small.getpixel((x,y))/256*10))] for x in range(small.width)).rstrip().center(48))

def E(s):
    import html
    return html.escape(str(s))

out=["""<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="720" viewBox="0 0 1250 720">
<rect width="100%" height="100%" rx="18" fill="#0d1117"/>
<rect x="20" y="20" width="1210" height="680" rx="14" fill="#161b22" stroke="#30363d"/>
<text x="55" y="70" fill="#f0883e" font-family="monospace" font-size="24">omar@github</text>
<text x="235" y="70" fill="#8b949e" font-family="monospace" font-size="22">────────────────────────────────────────────────────────────────────</text>
<text x="55" y="112" fill="#8b949e" font-family="monospace" font-size="18">┌───────────────────────┐</text>"""]
for i,line in enumerate(ascii_lines):
    out.append(f'<text x="58" y="{145+i*19}" fill="#e6edf3" font-family="monospace" font-size="16">{E(line)}</text>')
out.append(f'<text x="55" y="{145+len(ascii_lines)*19+10}" fill="#8b949e" font-family="monospace" font-size="18">└───────────────────────┘</text>')
rows=[("OS","Windows 11"),("Host","ASUS TUF Gaming A15"),("IDE","VS Code"),("Focus","Software Engineering"),("",""),("Languages.Programming","JavaScript, TypeScript, C++, Python"),("Languages.Web","React.js, Next.js, HTML, CSS"),("Backend","Node.js, Express.js, MongoDB"),("Cloud","AWS"),("",""),("Education","Tanta University — Computer Science"),("Graduation","Expected 2027")]
x0=620
for i,(label,value) in enumerate(rows):
    if not label: continue
    y=112+i*24; dots="................................"
    out.append(f'<text x="{x0}" y="{y}" font-family="monospace" font-size="16"><tspan fill="#f0883e">{E(label)}:</tspan><tspan fill="#8b949e"> {dots[:max(4,34-len(label))]} </tspan><tspan fill="#58a6ff">{E(value)}</tspan></text>')
y=112+len(rows)*24
out.append(f'<text x="{x0}" y="{y}" fill="#f0883e" font-family="monospace" font-size="18">- Contact ─────────────────────────────────────────────</text>')
for j,(label,value) in enumerate([("Email","omarlokma@gmail.com"),("LinkedIn","linkedin.com/in/omar-naguib"),("GitHub","github.com/Omarlokma")],1):
    yy=y+j*24; dots="................................"
    out.append(f'<text x="{x0}" y="{yy}" font-family="monospace" font-size="16"><tspan fill="#f0883e">{label}:</tspan><tspan fill="#8b949e"> {dots[:max(4,34-len(label))]} </tspan><tspan fill="#58a6ff">{E(value)}</tspan></text>')
y+=4*24
out.append(f'<text x="{x0}" y="{y}" fill="#f0883e" font-family="monospace" font-size="18">- GitHub Stats ────────────────────────────────────────</text>')
for j,(label,value) in enumerate([("Repositories",public_repos),("Stars",stars),("Commits",commits),("Followers",followers)],1):
    yy=y+j*24; dots="................................"
    out.append(f'<text x="{x0}" y="{yy}" font-family="monospace" font-size="16"><tspan fill="#f0883e">{label}:</tspan><tspan fill="#8b949e"> {dots[:max(4,34-len(label))]} </tspan><tspan fill="#58a6ff">{value}</tspan></text>')
out.append('<text x="55" y="678" fill="#8b949e" font-family="monospace" font-size="14">Updated automatically • github.com/Omarlokma</text>')
out.append("</svg>")
OUT.write_text("\n".join(out), encoding="utf-8")
