import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('app/app.py','r',encoding='utf-8') as f:
    lines=f.readlines()
for i,l in enumerate(lines,1):
    if 'page = "upload"' in l or "page = 'upload'" in l:
        print(i, l.rstrip()[:100])
