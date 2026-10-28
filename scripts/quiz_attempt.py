"""usage: quiz_attempt.py <quiz_id> show | precheck <slot> | submit <slot> | finish   (respostas em ~/Documentos/moodle-workflows/quiz-answers/<quiz>/slot<N>.c)"""
import asyncio, os, re, html, json, sys
for line in open('/home/gabriel-baldo/moodle-workflow-project/.env'):
    k,_,v=line.rstrip('\n').partition('=')
    if k in('MOODLE_URL','MOODLE_TOKEN'): os.environ[k]=v.strip().strip('"\'')
from moodle_mcp.server import _call
S=os.path.expanduser('~/Documentos/moodle-workflows/quiz-answers')
quiz=int(sys.argv[1]); cmd=sys.argv[2]; slot=int(sys.argv[3]) if len(sys.argv)>3 else None
AD=f'{S}/{quiz}'; os.makedirs(AD,exist_ok=True)
def txt(h):
    t=re.sub(r'<br\s*/?>|</tr>|</p>|</pre>|</li>','\n',h); t=html.unescape(re.sub(r'<[^>]+>','',t)); return re.sub(r'\n\s*\n+','\n',t).strip()
async def attempt():
    r=await _call('mod_quiz_get_user_attempts',quizid=quiz,status='unfinished')
    if r.get('attempts'): return r['attempts'][0]
    r=await _call('mod_quiz_start_attempt',quizid=quiz); print('NOVA TENTATIVA',r['attempt']['attempt'],r.get('warnings')); return r['attempt']
async def questions(att):
    out=[]; pages=sorted(set(int(p) for p in range(0,max(1,len(set(att['layout'].replace(',0','').split(',')))))))
    seen=set()
    for p in range(0,20):
        r=await _call('mod_quiz_get_attempt_data',attemptid=att['id'],page=p)
        if not r.get('questions'): break
        for q in r['questions']:
            if q['slot'] not in seen: seen.add(q['slot']); out.append(q)
        if r.get('nextpage',-1)==-1: break
    return out
def fields(q):
    h=q['html']; m=re.search(r'name="(q\d+:\d+_):flagged"',h); pre=m.group(1)
    seq=re.search(r'name="'+re.escape(pre)+r':sequencecheck" value="(\d+)"',h).group(1)
    return pre,seq
async def main():
    att=await attempt(); qs=await questions(att)
    print('attempt',att['id'],'nº',att['attempt'],att['state'],'| questões:',len(qs))
    if cmd=='show':
        for q in qs:
            h=q['html']; pre,seq=fields(q)
            ta=re.search(r'<textarea[^>]*>(.*?)</textarea>',h,re.S)
            print(f"\n===== SLOT {q['slot']} type={q['type']} =====")
            body=re.search(r'<div class="formulation clearfix">(.*?)<div class="ablock',h,re.S)
            print(txt(re.sub(r'<textarea.*?</textarea>','[[BOX]]',(body.group(1) if body else h),flags=re.S))[:3500])
            if ta:
                p=f'{AD}/slot{q["slot"]}.tpl.c'; open(p,'w').write(html.unescape(ta.group(1)).replace('\r',''))
                print('\n[template salvo em',p,']')
        return
    data=[]
    for q in qs:
        pre,seq=fields(q); f=f'{AD}/slot{q["slot"]}.c'
        if os.path.exists(f): data.append({'name':pre+'answer','value':open(f).read()})
        data.append({'name':pre+':sequencecheck','value':seq})
        if slot==q['slot'] and cmd in('precheck','submit'): data.append({'name':pre+'-'+cmd,'value':'1'})
    r=await _call('mod_quiz_process_attempt',attemptid=att['id'],data=data,finishattempt=1 if cmd=='finish' else 0,timeup=0)
    print('state:',r.get('state'),r.get('warnings'))
    if cmd!='finish':
        for q in await questions(att):
            if q['slot']==slot:
                h=q['html']; m=re.search(r'<div class="specificfeedback">.*',h,re.S) or re.search(r'<div class="outcome.*',h,re.S)
                print(txt(m.group(0))[-2500:] if m else 'sem feedback; estado: '+re.search(r'class="state">([^<]*)',h).group(1))
asyncio.run(main())
