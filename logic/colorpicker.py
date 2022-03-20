import os
import sys
import json
from subprocess import check_output, DEVNULL


def pick_color(default_color_rgb=(0.5, 0.5, 0.5)):
    '''Run the color picker, returning the color.
    Input and output are in normalized RGB (floating point [0,1]).
    '''
    args_json = json.dumps({'defaultColor': default_color_rgb})
    res_json = check_output((
        'osascript', '-l', 'JavaScript', '-s', 'o', '-e',
        f'''
        const app = Application.currentApplication();
        app.includeStandardAdditions = true;
        const rgb = app.chooseColor({args_json});
        JSON.stringify(rgb);
        '''
    ), text=True)
    r, g, b = json.loads(res_json)
    return (r, g, b)


if __name__ == '__main__':
    action_template = sys.argv[1:]
    assert any('<color>' in w for w in action_template)

    # convert normalized float components in [0,1] to hex string, like "ff00ff".
    rgb_hex = ''.join(f'{round(0xff * c):02x}' for c in pick_color())

    action = ' '.join(w.replace('<color>', rgb_hex) for w in action_template)

    return check_output(
        ('osascript', '-e', f'tell application "Alfred" to search "hue {action}"'),
        text=True,
    )
