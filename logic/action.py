import colorsys
import datetime
import json
import os
import random
import sys
import time

from .colorpicker import run_colorpicker
from . import colors
from . import harmony
from . import request
from . import setup
from . import utils


class HueAction:

    def __init__(self, workflow):
        self.workflow = workflow
        self.hue_request = request.HueRequest(workflow)

    def _get_xy_color(self, color, gamut):
        """Validate and convert hex color to XY space."""
        return colors.Converter(gamut).hex_to_xy(utils.get_color_value(color))

    def _get_random_xy_color(self, gamut):
        random_color = colorsys.hsv_to_rgb(random.random(), 1, 1)
        random_color = tuple([255 * x for x in random_color])
        return colors.Converter(gamut).rgb_to_xy(*random_color)

    def _set_palette(self, lids, palette):
        for index, lid in enumerate(lids):
            self.hue_request.request(
                'put',
                '/lights/%s/state' % lid,
                json.dumps({'xy': palette[index]})
            )

    def _shuffle_group(self, group_id):
        lights = utils.get_lights(self.workflow)
        lids = utils.get_group_lids(self.workflow, group_id)

        # Only shuffle the lights that are on
        on_lids = [lid for lid in lids if lights[lid]['state']['on']]
        on_xy = [lights[lid]['state']['xy'] for lid in on_lids]
        shuffled = list(on_xy)

        # Shuffle until all indexes are different (generate a derangement)
        while not all([on_xy[i] != shuffled[i] for i in range(len(on_xy))]):
            random.shuffle(shuffled)

        self._set_palette(on_lids, shuffled)

    def _set_harmony(self, group_id, mode, root):
        lights = utils.get_lights(self.workflow)
        lids = utils.get_group_lids(self.workflow, group_id)
        palette = []

        on_lids = [lid for lid in lids if lights[lid]['state']['on']]
        args = (len(on_lids), '#%s' % utils.get_color_value(root))
        harmony_colors = getattr(harmony, mode)(*args)

        for lid in on_lids:
            gamut = colors.get_light_gamut(lights[lid]['modelid'])
            xy = self._get_xy_color(harmony_colors.pop(), gamut)
            palette.append(xy)

        self._set_palette(on_lids, palette)

    def execute(self, action):
        is_light = action[0] == 'lights'
        is_group = action[0] == 'groups'

        if not is_light and not is_group:
            return

        rid = action[1]
        function = action[2]
        value = action[3] if len(action) > 3 else None
        lights = utils.get_lights(self.workflow)
        groups = utils.get_groups(self.workflow)

        # Default API request parameters
        method = 'put'
        endpoint = '/groups/%s/action' % rid if is_group else '/lights/%s/state' % rid

        if function == 'off':
            data = {'on': False}

        elif function == 'on':
            data = {'on': True}

        elif function == 'bri':
            value = int((float(value) / 100) * 255) if value else 255
            data = {'bri': value}

        elif function == 'shuffle':
            if not is_group:
                print('Shuffle can only be called on groups.')
                return

            self._shuffle_group(rid)
            return True

        elif function == 'rename':
            endpoint = '/groups/%s' % rid if is_group else '/lights/%s' % rid
            data = {'name': value}

        elif function == 'effect':
            data = {'effect': value}

        elif function == 'color':
            if value == 'random':
                if is_group:
                    gamut = colors.GamutA
                    data = {'xy': self._get_random_xy_color(gamut)}
                else:
                    gamut = colors.get_light_gamut(lights[rid]['modelid'])
                    data = {'xy': self._get_random_xy_color(gamut)}
            else:
                try:
                    if is_group:
                        gamut = colors.GamutA
                    else:
                        gamut = colors.get_light_gamut(lights[rid]['modelid'])
                    data = {'xy': self._get_xy_color(value, gamut)}
                except ValueError:
                    print('Error: Invalid color. Please use a 6-digit hex color.')
                    return

        elif function == 'harmony':
            if not is_group:
                print('Color harmonies can only be set on groups.')
                return

            root = action[4] if len(action) > 3 else None

            if value not in harmony.MODES:
                print('Invalid harmony mode.')
                return

            self._set_harmony(rid, value, root)
            return

        elif function == 'reminder':
            try:
                time_delta_int = int(value)
            except ValueError:
                print('Error: Invalid time delta for reminder.')
                return

            reminder_time = datetime.datetime.utcfromtimestamp(time.time() + time_delta_int)

            method = 'post'
            data = {
                'name': 'Alfred Hue Reminder',
                'command': {
                    'address': self.hue_request.api_path + endpoint,
                    'method': 'PUT',
                    'body': {'alert': 'lselect'},
                },
                'time': reminder_time.replace(microsecond=0).isoformat(),
            }
            endpoint = '/schedules'

        elif function == 'set':
            # if bridge is deconz, scenes are set differently.
            # what we need is groups:group_id:scenes:scene_id:recall
            is_deconz = False
            try:
                if workflow.stored_data("full_state")["config"]["modelid"] == "deCONZ":
                    is_deconz = True
            except:
                # not sure if hue also returns config/modelid
                pass

            if is_deconz:
                method = 'put'
                endpoint = '/groups/{}/scenes/{}/recall'.format(rid, value)
                data = {}
            else:
                data = {'scene': value}


        elif function == 'save':
            lids = utils.get_group_lids(self.workflow, rid)
            method = 'post'
            endpoint = '/scenes'
            data = {'name': value, 'lights': lids, 'recycle': False}

        else:
            return

        # Make the request
        self.hue_request.request(method, endpoint, json.dumps(data))

        return


def run_action(workflow):
    if workflow.args[1] == 'colorpicker':
        return run_colorpicker(workflow)

    # Handle multiple queries separated with '|' (pipe) character
    queries = workflow.args[1].split('|')

    for query_str in queries:
        query = query_str.split(':')
        if query[0] == 'set_bridge':
            setup.set_bridge(workflow, query[1] if len(query) > 1 else None)
        else:
            action = HueAction(workflow)
            try:
                action.execute(query)
                print('Action completed! <%s>' % query_str)
            except ValueError:
                pass
