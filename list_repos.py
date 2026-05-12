import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit(
            "ERROR: 環境変数 GITHUB_TOKEN が設定されていません。\n"
            "  PowerShell:  $env:GITHUB_TOKEN = 'ghp_xxx'\n"
            "  cmd:         set GITHUB_TOKEN=ghp_xxx\n"
            "トークンは https://github.com/settings/tokens から発行できます (scope: repo)。"
        )
    return token


def fetch_repos(token: str):
    repos = []
    page = 1
    while True:
        url = f"{API}/user/repos?per_page=100&page={page}&affiliation=owner&sort=updated"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "list-repos-script",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                batch = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"GitHub API エラー: {e.code} {e.reason}\n{e.read().decode(errors='replace')}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def main():
    repos = fetch_repos(get_token())
    print(f"{len(repos)} 件のリポジトリ:\n")
    for r in repos:
        visibility = "private" if r["private"] else "public"
        lang = r.get("language") or "-"
        print(f"  {r['full_name']:<50} [{visibility:<7}] {lang:<12} {r['html_url']}")


if __name__ == "__main__":
    main()
