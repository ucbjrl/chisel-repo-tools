'''
Created on Jan 10, 2017

@author: jrl
'''

def traffic_clones(ghr, period):
    """Retrieve the traffic counts for a repo.


    The dictionary returned has three entries: ``count``, ``uniques``, and an array of ``clones``.

    :returns: dict
    """
    url = ghr._build_url('traffic', 'clones', base_url=ghr._api)
    params = { 'per': period }
    resp = ghr._get(url, params=params)
    if resp.status_code == 202:
        return {}
    json = ghr._json(resp, 200)
    if json.get('ETag'):
        del json['ETag']
    if json.get('Last-Modified'):
        del json['Last-Modified']
    return json
