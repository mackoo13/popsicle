"""
fake-bash scripts are meant to display a helpful and compassionate message
"""


def display_message(script_name):
    print('Warning: ' + script_name + ' is a Bash script and should be invoked with extension:\n'
          + script_name + '.sh')


def exec():
    display_message('popsicle-exec')


def predict():
    display_message('popsicle-predict')
