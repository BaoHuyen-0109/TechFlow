"""Sequential browser acceptance; screenshots kept local with a bounded evidence set."""
import os
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    env=dict(os.environ)
    env.pop('TECHFLOW_SCREENSHOT_DIR',None)
    jobs=[['verify_warranties_ui.py'],['verify_inventory_ui.py'],['verify_customers_ui.py'],
          ['verify_dashboard_ui.py'],['verify_ui.py','--screenshot-prefix','stage52-regression'],
          ['verify_catalog_ui.py','--screenshot-prefix','stage52-catalog'],['verify_catalog_polish.py']]
    parser=argparse.ArgumentParser()
    parser.add_argument('--start-at',choices=[job[0] for job in jobs],default=jobs[0][0])
    start_at=parser.parse_args().start_at
    start_index=[job[0] for job in jobs].index(start_at)
    for index,job in enumerate(jobs):
        if index<start_index:continue
        if index:env['TECHFLOW_SCREENSHOT_DIR']=str(ROOT/'.docker-local/stage52-regression-screenshots')
        if index:time.sleep(35)  # Let the shared real login limiter replenish between suites.
        start=time.monotonic()
        subprocess.run([sys.executable,str(ROOT/'scripts'/job[0]),*job[1:]],cwd=ROOT,env=env,check=True)
        print(job[0]+f' passed in {time.monotonic()-start:.1f}s',flush=True)
    print(f'All {len(jobs)-start_index} selected browser suites passed; no demo fixtures or volume deletion.')


if __name__=='__main__':main()
