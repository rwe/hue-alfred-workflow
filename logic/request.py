import requests


class HueRequest():
    """Handles Philips Hue API path strings and logs every request for debugging."""

    def __init__(self, workflow):
        self.workflow = workflow
        self.api_path = '/api/%s' % self.workflow.settings['username']
        self.api_path_full = 'http://{bridge_ip}{api_path}'.format(
            bridge_ip=self.workflow.settings['bridge_ip'],
            api_path=self.api_path,
        )

    def request(self, method, endpoint, data=None):
        self.workflow.logger.info('request({method}, {endpoint}, {data})'.format(
            method=method, endpoint=endpoint, data=data,
        ))
        return requests.request(method, self.api_path_full + endpoint, data=data)
