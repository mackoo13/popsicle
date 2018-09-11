import os


def check_config(var_names):
    if type(var_names) is str:          # Accidental call with 'var' instead of ['var']
        var_names = [var_names]

    for var in var_names:
        if var not in os.environ:
            raise EnvironmentError(
                var + ' environment variable not found. Check your config and run it with \'source\' command.'
            )
