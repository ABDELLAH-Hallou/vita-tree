"""Synthetic provider-check v1 writer. Never imports or contacts a provider."""
import json
import os
from pathlib import Path
import sys
import subprocess
import time

args=sys.argv[1:]
assert args[:2]==['providers','check'] and '--generate' in args and '--json' in args
provider=args[args.index('--provider')+1]
model=args[args.index('--model')+1] if '--model' in args else 'fixture-default'
assert not Path('main.tex').exists() and not Path('job.md').exists()
assert not Path('.vita/.env').exists()
# Windows may retain an 8.3 alias in cwd while resolve() expands it. Compare
# directory identity so the isolation assertion accepts either spelling.
assert Path(os.environ['VITA_PROJECT_ROOT']).samefile(Path.cwd())
settings=json.loads(Path('.vita/extensions.json').read_text(encoding='utf-8'))
assert set(settings)=={'llm_providers'} and set(settings['llm_providers'])=={provider}
assert settings['llm_providers'][provider]['model']==('' if model=='fixture-default' else model)
if os.environ.get('VITA_TEST_CHECK_CALLS'):
    with Path(os.environ['VITA_TEST_CHECK_CALLS']).open('a',encoding='utf-8') as log: log.write(provider+' / '+model+'\n')
if provider=='codex':
    assert Path('.git').is_dir()
    actual=subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True,encoding='utf-8').strip()
    assert Path(actual).resolve()==Path.cwd().resolve()
    assert not Path('AGENTS.md').exists()
    assert settings['llm_providers'][provider].get('reasoning_effort','')==os.environ['VITA_TREE_REASONING']
if model=='slow': time.sleep(.4)
category=model if model in {'overloaded','authentication','rate_limit','invalid_model','invalid_json'} else None
error={'schema_version':1,'code':'provider_error','category':category,'provider':provider,'model':model,
       'retryable':category in {'overloaded','rate_limit'},'attempts':3 if category=='overloaded' else 1,
       'max_attempts':3,'exhausted':category=='overloaded','status':503 if category=='overloaded' else 401,
       'action':'RAW-PRIVATE-PROMPT','raw':'PRIVATE-KEY'} if category else None
result={'schema_version':1,'check':'generation','status':'failed' if error else 'success',
        'generation_verified':not bool(error),'may_consume_usage':True,'attempts':error['attempts'] if error else 1,
        'provider':provider,'model':model,'error':error,'raw':'RAW-PRIVATE-PROMPT',
        'env':dict(os.environ)}
if model=='secret':
    result.update(status='failed',generation_verified=False,model=os.environ.get('GEMINI_API_KEY'))
    result['error']={**(error or {}),'schema_version':1,'code':'provider_error','category':'authentication',
                     'provider':provider,'model':os.environ.get('GEMINI_API_KEY'),'retryable':False}
if model=='future': result['schema_version']=2
if model=='wrong-route': result['provider']='openai'
if model=='unreported': result['provider']=None
folder=Path('.vita/results');folder.mkdir(parents=True)
(folder/'provider-check.json').write_text(json.dumps(result),encoding='utf-8')
print('PRIVATE-STDOUT-KEY')
print('PRIVATE-STDERR-KEY',file=sys.stderr)
raise SystemExit(1 if not result['generation_verified'] else 0)
