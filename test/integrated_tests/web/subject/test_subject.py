
import pytest

from yosai.core import (
    AuthenticationException,
    ExpiredSessionException,
    IdentifiersNotSetException,
    IllegalStateException,
    event_bus,
)

from yosai.web import WebYosai


def test_subject_invalid_login(web_yosai, mock_web_registry,
                               invalid_username_password_token):

    with pytest.raises(AuthenticationException):

        with WebYosai.context(web_yosai, mock_web_registry):
            subject = WebYosai.get_current_subject()
            subject.login(invalid_username_password_token)


def test_authenticated_subject_is_permitted(
        web_yosai, mock_web_registry, valid_username_password_token,
        thedude_testpermissions):

    tp = thedude_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        results = new_web_subject.is_permitted(tp['perms'])
        assert results == tp['expected_results']

        new_web_subject.logout()

        with pytest.raises(IdentifiersNotSetException):
            new_web_subject.is_permitted(tp['perms'])


def test_authenticated_subject_is_permitted_collective(
        web_yosai, mock_web_registry, valid_username_password_token,
        thedude_testpermissions):

    tp = thedude_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        assert ((new_web_subject.is_permitted_collective(tp['perms'], any) is True) and
                (new_web_subject.is_permitted_collective(tp['perms'], all) is False))

        new_web_subject.logout()

        with pytest.raises(IdentifiersNotSetException):
            new_web_subject.is_permitted_collective(tp['perms'], any)


def test_has_role(web_yosai, mock_web_registry, valid_username_password_token,
                  thedude_testroles):

    tr = thedude_testroles
    event_detected = None

    def event_listener(identifiers=None, items=None):
        nonlocal event_detected
        event_detected = items
    event_bus.register(event_listener, 'AUTHORIZATION.RESULTS')

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        result = new_web_subject.has_role(tr['roles'])

        assert (tr['expected_results'] == result and
                frozenset(event_detected) == result)

        new_web_subject.logout()


def test_authenticated_subject_has_role_collective(
        web_yosai, mock_web_registry, valid_username_password_token,
        thedude_testroles):

    tr = thedude_testroles

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        assert ((new_web_subject.has_role_collective(tr['roles'], all) is False) and
                (new_web_subject.has_role_collective(tr['roles'], any) is True))

        new_web_subject.logout()


def test_run_as_raises(web_yosai, mock_web_registry, walter_identifier):

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        # a login is required , so this should raise:
        with pytest.raises(IllegalStateException):
            new_web_subject.run_as(walter_identifier)


def test_run_as_pop(walter_identifier, jackie_identifier, web_yosai, mock_web_registry,
                    jackie_testpermissions, walter_testpermissions,
                    valid_username_password_token):

    jp = jackie_testpermissions
    wp = walter_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        new_web_subject.run_as(jackie_identifier)
        jackieresults = new_web_subject.is_permitted(jp['perms'])
        assert jackieresults == jp['expected_results']

        new_web_subject.run_as(walter_identifier)
        walterresults = new_web_subject.is_permitted(wp['perms'])
        assert walterresults == wp['expected_results']

        new_web_subject.pop_identity()
        assert new_web_subject.identifiers == jackie_identifier

        new_web_subject.logout()


def test_logout_clears_cache(
        thedude_identifier, web_yosai, mock_web_registry,
        valid_username_password_token, thedude_testpermissions, caplog):

    tp = thedude_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        new_web_subject.is_permitted(tp['perms'])  # caches authz_info

        new_web_subject.logout()

        out = caplog.text

        assert ('Clearing cached credentials for [thedude]' in out and
                'Clearing cached authz_info for [thedude]' in out)


def test_session_stop_clears_cache(
        thedude_identifier, mock_web_registry, web_yosai,
        valid_username_password_token, thedude_testpermissions, caplog):

    tp = thedude_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        new_web_subject.is_permitted(tp['perms'])  # caches authz_info

        session = new_web_subject.get_session()
        session.stop(None)

        out = caplog.text

        assert ('Clearing cached credentials for [thedude]' in out and
                'Clearing cached authz_info for [thedude]' in out)


def test_login_clears_cache(
        thedude_identifier, valid_username_password_token, caplog, web_yosai,
        mock_web_registry):

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        out = caplog.text

        assert 'Clearing cached authz_info for [thedude]' in out
        new_web_subject.logout()

def test_session_idle_expiration_clears_cache(
        thedude_identifier, valid_username_password_token, thedude_testpermissions,
        caplog, web_yosai, mock_web_registry):

    cache_handler = web_yosai.security_manager.session_manager.session_handler.\
        session_store.cache_handler

    tp = thedude_testpermissions

    with WebYosai.context(web_yosai, mock_web_registry):
        new_web_subject = WebYosai.get_current_subject()
        new_web_subject.login(valid_username_password_token)

        new_web_subject.is_permitted(tp['perms'])  # caches authz_info

        session = new_web_subject.get_session()
        session = cache_handler.get('session', identifier=session.session_id)

        twenty_ago = (60 * 20 * 1000)
        session.last_access_time = session.last_access_time - twenty_ago
        cache_handler.set('session', session.session_id, session)
        session = cache_handler.get('session', identifier=session.session_id)

        session = new_web_subject.get_session()

        with pytest.raises(ExpiredSessionException):
            session.last_access_time  # this triggers the expiration

            out = caplot.text
            assert ('Clearing cached credentials for [thedude]' in out and
                    'Clearing cached authz_info for [thedude]' in out)

            new_web_subject.logout()
