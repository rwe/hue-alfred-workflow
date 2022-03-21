import sys
from .action import run_action
from .colorpicker import run_colorpicker
from .filters import run_filters

from workflow import Workflow3

def _main(argv):
    if len(argv) < 2:
        raise ValueError('Insufficient arguments')
    command_name = argv[1]
    if command_name == 'filter':
        workflow = Workflow3(update_settings={'github_slug': 'benknight/hue-alfred-workflow'})
        if workflow.update_available:
            workflow.add_item(
                'New version available!',
                'Press enter to install the update.',
                autocomplete='workflow:update')
        main = run_filters
    elif command_name == 'action':
        workflow = Workflow3()
        main = run_action
    else:
        raise ValueError('Invalid command %s', command_name)
    return workflow.run(main)


if __name__ == '__main__':
    sys.exit(_main(sys.argv))
