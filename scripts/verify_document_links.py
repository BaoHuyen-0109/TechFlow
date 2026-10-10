"""Check local Markdown file/image targets without contacting external websites."""
import re
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]


def main():
    broken=[];checked=0
    for document in [ROOT/'README.md',*(ROOT/'docs').rglob('*.md')]:
        content=document.read_text(encoding='utf-8-sig')
        for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)',content):
            target=match.group(1).strip().strip('<>')
            if target.startswith('#') or urlsplit(target).scheme:continue
            target=unquote(target.split('#')[0])
            checked+=1
            if target and not (document.parent/target).is_file():broken.append(str(document.relative_to(ROOT))+': '+target)
    if broken:raise SystemExit('Broken local links:\n'+'\n'.join(broken))
    print('Local documentation links passed:',checked,'file/image targets. External URLs not checked.')


if __name__=='__main__':main()
