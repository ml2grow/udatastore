import nox


@nox.session
def unit(session):
    session.interpreter = 'python3.6'
    session.install('pytest', 'mock')
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run('py.test', 'tests')

