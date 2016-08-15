from yosai.web import (
    WebYosai,
)
from yosai_alchemystore import AlchemyAccountStore
from yosai_dpcache.cache import DPCacheHandler

import os
import pytest


def test_create_yosai_instance(monkeypatch, web_yosai):
    """
    Create a new WebYosai instance from env_var settings and from file_path
    settings.  This subsequently creates a configured WebSecurityManager.
    web_yosai is configured using the file_path approach
    """
    current_filepath = os.path.dirname(__file__)
    settings_file = current_filepath + '/../../../yosai_settings.yaml'
    monkeypatch.setenv('TEST_ENV_VAR', settings_file)
    first_yosai = WebYosai(env_var='TEST_ENV_VAR')

    assert first_yosai._security_manager and web_yosai._security_manager


def test_webyosai_security_manager_configuration(web_yosai):
    """
    Assert that upon creation of a new WebYosai instance that the managers
    automatically generated using yaml settings are as expected.
    """

    # using a random sample:
    assert isinstance(web_yosai.security_manager.authorizer.realms[0].account_store,
                      AlchemyAccountStore)
    assert isinstance(web_yosai.security_manager.session_manager.session_handler.cache_handler,
                      DPCacheHandler)
    assert web_yosai.signed_cookie_secret == 'changeme'


def test_webyosai_requires_authentication(
        web_yosai, mock_web_registry, valid_username_password_token):
    """
    confirm authentication approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    @WebYosai.requires_authentication
    def transport_ransom(the_ringer, destination):
        return 'transported'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        subject.login(valid_username_password_token)
        result = transport_ransom('the_ringer', 'the_nihilists')

        assert result == 'transported'

        subject.logout()

        with pytest.raises(mock_web_registry.mock_exception):
            transport_ransom('the_ringer', 'the_nihilists')


def test_webyosai_requires_user(
        web_yosai, mock_web_registry, valid_username_password_token):
    """
    confirm user approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    @WebYosai.requires_user
    def transport_ransom(the_ringer, destination):
        return 'transported'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        subject.login(valid_username_password_token)
        result = transport_ransom('the_ringer', 'the_nihilists')

        assert result == 'transported'

        subject.logout()

        with pytest.raises(mock_web_registry.mock_exception):
            transport_ransom('the_ringer', 'the_nihilists')


def test_webyosai_requires_guest(
        web_yosai, mock_web_registry, valid_username_password_token):
    """
    confirm guest approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    @WebYosai.requires_guest
    def transport_ransom(the_ringer, destination):
        return 'transported'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        result = transport_ransom('the_ringer', 'the_nihilists')

        assert result == 'transported'

        subject.login(valid_username_password_token)

        with pytest.raises(mock_web_registry.mock_exception):
            transport_ransom('the_ringer', 'the_nihilists')


def test_webyosai_requires_permission(
        web_yosai, mock_web_registry, valid_username_password_token):
    """
    confirm permission approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    # the dude is a courier so he can transport the ringer but he's not a thief
    # so he can't access ransom

    @WebYosai.requires_permission(['leatherduffelbag:transport:theringer'])
    def transport_ransom(the_ringer, destination):
        return 'transported'

    @WebYosai.requires_permission(['leatherduffelbag:access:theringer'])
    def access_ransom(the_ringer):
        return 'accessed'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        subject.login(valid_username_password_token)

        result = transport_ransom('the_ringer', 'the_nihilists')
        assert result == 'transported'

        with pytest.raises(mock_web_registry.mock_exception):
            access_ransom('the_ringer')


def test_webyosai_requires_dynamic_permission(
        web_yosai, mock_web_registry, monkeypatch, valid_username_password_token):
    """
    confirm dynamic_permission approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    # the dude is a courier so he can transport the ringer but he's not a thief
    # so he can't access ransom

    monkeypatch.setitem(mock_web_registry.resource_params, 'resource', 'theringer')

    @WebYosai.requires_dynamic_permission(['leatherduffelbag:transport:{resource}'])
    def transport_ransom(the_ringer, destination):
        return 'transported'

    @WebYosai.requires_dynamic_permission(['leatherduffelbag:access:{resource}'])
    def access_ransom(the_ringer):
        return 'accessed'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        subject.login(valid_username_password_token)

        result = transport_ransom('the_ringer', 'the_nihilists')
        assert result == 'transported'

        with pytest.raises(mock_web_registry.mock_exception):
            access_ransom('the_ringer')


def test_webyosai_requires_role(
        web_yosai, mock_web_registry, valid_username_password_token):
    """
    confirm role approved and denied
    """
    # yeah, it's a dumb example but I chose the big lebowski cuz I love the movie
    # the dude is a courier so he can transport the ringer but he's not a thief
    # so he can't access ransom

    @WebYosai.requires_role(['courier'])
    def transport_ransom(the_ringer, destination):
        return 'transported'

    @WebYosai.requires_role(['thief'])
    def access_ransom(the_ringer):
        return 'accessed'

    with WebYosai.context(web_yosai, mock_web_registry):
        subject = WebYosai.get_current_subject()
        subject.login(valid_username_password_token)

        result = transport_ransom('the_ringer', 'the_nihilists')
        assert result == 'transported'

        with pytest.raises(mock_web_registry.mock_exception):
            access_ransom('the_ringer')