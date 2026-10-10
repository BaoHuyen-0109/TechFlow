"""Verify real Nginx/Gunicorn access logs omit query/referrer on test service."""
from datetime import datetime,timezone
import secrets
import subprocess
import time
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def main():
    marker='PRIVACY-CHECK-'+secrets.token_hex(12)
    since=datetime.now(timezone.utc).isoformat()
    request=Request('http://localhost:8001/business/warranties/lookup?q='+marker,
        headers={'Referer':'http://localhost:8001/referrer/'+marker})
    try:build_opener(NoRedirect()).open(request,timeout=10)
    except HTTPError as error:assert error.code==302
    time.sleep(1)
    for service in ['ui','ui-nginx']:
        logs=subprocess.check_output(['docker','compose','-f','docker-compose.db-test.yml','logs','--since',since,service],text=True)
        assert '/business/warranties/lookup' in logs,'Expected request was not logged: '+service
        assert marker not in logs,'Query/referrer leaked into '+service+' access logs'
    print('Real Nginx and Gunicorn access logs omit query strings and referrers.')


if __name__=='__main__':main()
