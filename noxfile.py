import nox


@nox.session(python="3.6")
def unit(session):
    session.install('pytest', 'mock', 'pytest-spec')
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run('py.test', '--spec', 'tests')

