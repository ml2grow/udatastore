# pylint: skip-file
import nox


@nox.session(python="3.6")
def unit(session):
    session.install('pytest', 'mock', 'pytest-spec')
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run('py.test', '--spec', 'tests')


@nox.session(python="3.6")
def lint(session):
    session.install('pylint')
    session.install('pylint_runner')
    session.install('-e', '.')

    session.run('pylint_runner', 'udatastore')
