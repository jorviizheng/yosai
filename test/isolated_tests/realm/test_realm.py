import pytest

from yosai.core import (
    Account,
    AccountStoreRealm,
    AuthzInfoNotFoundException,
    CacheCredentialsException,
    ClearCacheCredentialsException,
    CredentialsNotFoundException,
    GetCachedCredentialsException,
    IndexedAuthorizationInfo,
    IncorrectCredentialsException,
    InvalidArgumentException,
    PasswordVerifier,
    RealmMisconfiguredException,
    SimpleIdentifierCollection,
)
from ..doubles import (
    MockAccount,
    MockAccountStore,
)

from unittest import mock

# -----------------------------------------------------------------------------
# AccountStoreRealm Tests
# -----------------------------------------------------------------------------

def test_asr_authzinforesolver_set(monkeypatch, default_accountstorerealm):
    asr = default_accountstorerealm

    monkeypatch.setattr(asr, 'account_store', mock.Mock())
    asr.authz_info_resolver = 'authz_info_resolver'
    assert (asr._authz_info_resolver == 'authz_info_resolver' and
            asr.account_store.authz_info_resolver == 'authz_info_resolver')


def test_asr_credentialresolver_set(monkeypatch, default_accountstorerealm):
    asr = default_accountstorerealm

    monkeypatch.setattr(asr, 'account_store', mock.Mock())
    asr.credential_resolver = 'credential_resolver'
    assert (asr._credential_resolver == 'credential_resolver' and
            asr.account_store.credential_resolver == 'credential_resolver')


def test_asr_permissionresolver_set(monkeypatch, default_accountstorerealm):
    asr = default_accountstorerealm

    monkeypatch.setattr(asr, 'account_store', mock.Mock())
    monkeypatch.setattr(asr, 'permission_verifier', mock.Mock())

    asr.permission_resolver = 'permission_resolver'

    assert (asr._permission_resolver == 'permission_resolver' and
            asr.account_store.permission_resolver == 'permission_resolver' and
            asr.permission_verifier.permission_resolver == 'permission_resolver')


def test_asr_roleresolver_set(monkeypatch, default_accountstorerealm):
    asr = default_accountstorerealm

    monkeypatch.setattr(asr, 'account_store', mock.Mock())
    asr.role_resolver = 'role_resolver'
    assert (asr._role_resolver == 'role_resolver' and
            asr.account_store.role_resolver == 'role_resolver')


def test_asr_do_clear_cache(default_accountstorerealm):
    """
    unit tested:  do_clear_cache

    test case:
    in turn calls the clear cache methods for credentials and authz info
    """
    asr = default_accountstorerealm
    with mock.patch.object(AccountStoreRealm, 'clear_cached_credentials') as ccc:
        ccc.return_value = None

        with mock.patch.object(AccountStoreRealm,
                               'clear_cached_authorization_info') as ccai:
            ccai.return_value = None

            asr.do_clear_cache('identifier')

            ccc.assert_called_once_with('identifier')
            ccai.assert_called_once_with('identifier')


def test_asr_clear_cached_credentials(default_accountstorerealm, monkeypatch):
    """
    unit tested: clear_cached_credentials

    test case:
    delegates to cch.clear_cache
    """
    asr = default_accountstorerealm
    monkeypatch.setattr(asr, 'cache_handler', mock.Mock())
    asr.clear_cached_credentials('identifier')
    asr.cache_handler.delete.assert_called_once_with('credentials', 'identifier')


def test_asr_clear_cached_authorization_info(
        default_accountstorerealm, monkeypatch):
    """
    unit tested: clear_cached_authorization_info

    test case:
    delegates to ach.clear_cache
    """
    asr = default_accountstorerealm
    monkeypatch.setattr(asr, 'cache_handler', mock.Mock())
    asr.clear_cached_authorization_info('identifier')
    asr.cache_handler.delete.assert_called_once_with('authz_info', 'identifier')


def test_asr_get_credentials_from_cache(
        default_accountstorerealm, monkeypatch):
    asr = default_accountstorerealm
    mock_cache = mock.Mock()
    mock_cache.get_or_create.return_value = 'cached_creds'
    monkeypatch.setattr(asr, 'cache_handler', mock_cache)
    result = asr.get_credentials('identifier')
    assert (result.account_id == 'identifier' and
            result.credentials == 'cached_creds')


def test_asr_get_credentials_with_cache_but_from_accountstore(
        default_accountstorerealm, monkeypatch):
    asr = default_accountstorerealm
    monkeypatch.setattr(asr, 'cache_handler', None)
    result = asr.get_credentials('identifier')
    assert result.credentials == 'stored_creds'


def test_asr_get_credentials_without_cache_from_accountstore(
        default_accountstorerealm, monkeypatch):
    asr = default_accountstorerealm
    monkeypatch.setattr(asr, 'cache_handler', None)
    result = asr.get_credentials('identifier')
    assert result.credentials == 'stored_creds'


def test_asr_get_credentials_cannot_locate(
        default_accountstorerealm, monkeypatch):
    asr = default_accountstorerealm
    monkeypatch.setattr(asr, 'cache_handler', None)
    monkeypatch.setattr(asr.account_store, 'get_credentials', lambda x: None)

    with pytest.raises(CredentialsNotFoundException):
        asr.get_credentials('identifier')


def test_asr_authenticate_account_invalidtoken(default_accountstorerealm):
    asr = default_accountstorerealm

    with pytest.raises(InvalidArgumentException):
        asr.authenticate_account('invalid_token')


def test_asr_authenticate_account(username_password_token,
                                  default_accountstorerealm,
                                  full_mock_account, monkeypatch,
                                  simple_identifier_collection):

    token = username_password_token
    pasr = default_accountstorerealm
    fma = full_mock_account
    sic = simple_identifier_collection

    monkeypatch.setattr(pasr, 'get_credentials', lambda x: fma)
    with mock.patch.object(AccountStoreRealm, 'assert_credentials_match') as acm:
        acm.return_value = None
        result = pasr.authenticate_account(token)
        acm.assert_called_once_with(token, fma)
        fma.account_id = sic
        assert result == fma


def test_asr_acm_succeeds(username_password_token, default_accountstorerealm,
                          full_mock_account):
    """
    unit tested:  assert_credentials_match

    test case:
    when credentials match, nothing is returned nor any exceptions raise
    """
    token = username_password_token
    asr = default_accountstorerealm

    with mock.patch.object(PasswordVerifier, 'credentials_match') as pm_cm:
        pm_cm.return_value = True
        asr.assert_credentials_match(token, full_mock_account)
        pm_cm.assert_called_once_with(token, full_mock_account)


def test_asr_acm_raises(username_password_token, default_accountstorerealm,
                        full_mock_account):
    """
    unit tested:  assert_credentials_match

    test case:
    when credentials fail to match, an exception is raised
    """
    token = username_password_token
    asr = default_accountstorerealm

    with pytest.raises(IncorrectCredentialsException):
        with mock.patch.object(PasswordVerifier, 'credentials_match') as pm_cm:
            pm_cm.return_value = False
            asr.assert_credentials_match(token, full_mock_account)


def test_asr_get_authz_info_from_cache(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):

    sic = simple_identifier_collection
    asr = default_accountstorerealm

    mock_cache = mock.Mock()
    mock_cache.get_or_create.return_value = 'cached_authz_info'
    monkeypatch.setattr(asr, 'cache_handler', mock_cache)

    result = asr.get_authorization_info(sic)

    assert (result.account_id == 'identifier' and
            result.authz_info == 'cached_authz_info')


def test_asr_get_authz_info_with_cache_but_from_accountstore(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):
    asr = default_accountstorerealm
    sic = simple_identifier_collection
    monkeypatch.setattr(asr, 'cache_handler', None)

    result = asr.get_authorization_info(sic)
    assert result.authz_info == 'stored_authzinfo'


def test_asr_get_authz_info_without_cache_from_accountstore(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):
    asr = default_accountstorerealm
    sic = simple_identifier_collection
    monkeypatch.setattr(asr, 'cache_handler', None)
    result = asr.get_authorization_info(sic)
    assert result.authz_info == 'stored_authzinfo'


def test_asr_get_authz_info_cannot_locate(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):
    asr = default_accountstorerealm
    sic = simple_identifier_collection
    monkeypatch.setattr(asr, 'cache_handler', None)
    monkeypatch.setattr(asr.account_store, 'get_authz_info', lambda x: None)

    with pytest.raises(AuthzInfoNotFoundException):
        asr.get_authorization_info(sic)


def test_asr_is_permitted_yields(
        default_accountstorerealm, monkeypatch, full_mock_account,
        simple_identifier_collection):
    """
    unit tested:  is_permitted

    test case:
    - gets authorization info
    - yields from the permission_verifier, one permission at a time
    """
    asr = default_accountstorerealm
    sic = simple_identifier_collection

    def mock_yielder(authz_info, input):
        yield ('permission', True)

    monkeypatch.setattr(asr, 'get_authorization_info', lambda x: full_mock_account)
    monkeypatch.setattr(asr.permission_verifier, 'is_permitted', mock_yielder)

    results = list(asr.is_permitted(sic, ['domain:action']))
    assert results == [('permission', True)]


def test_asr_is_permitted_no_account_obtained(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):
    """
    unit tested:  is_permitted

    test case:
    - no account can be obtained from  get_authorization_info
    - yields False for each permission requested
    """
    asr = default_accountstorerealm
    sic = simple_identifier_collection

    monkeypatch.setattr(asr, 'get_authorization_info', lambda x: None)

    results = list(asr.is_permitted(sic, ['domain1:action1', 'domain2:action1']))
    assert results == [('domain1:action1', False), ('domain2:action1', False)]


def test_asr_has_role_yields(
        default_accountstorerealm, monkeypatch, simple_identifier_collection,
        full_mock_account):
    """
    unit tested:  has_role

    test case:
    - gets authorization info
    - yields from the role_verifier, one role at a time
    """
    asr = default_accountstorerealm
    sic = simple_identifier_collection

    def mock_yielder(authz_info, input):
        yield ('roleid1', False)

    monkeypatch.setattr(asr, 'get_authorization_info', lambda x: full_mock_account)
    monkeypatch.setattr(asr.role_verifier, 'has_role', mock_yielder)

    results = list(asr.has_role(sic, {'roleid1'}))
    assert results == [('roleid1', False)]


def test_asr_has_role_no_account_obtained(
        default_accountstorerealm, monkeypatch, simple_identifier_collection):
    """
    unit tested:  has_role

    test case:
    - no account can be obtained from  get_authorization_info
    - yields False for each role requested
    """
    asr = default_accountstorerealm
    sic = simple_identifier_collection

    monkeypatch.setattr(asr, 'get_authorization_info', lambda x: None)

    results = list(asr.has_role(sic, ['role1', 'role2']))
    assert results == [('role1', False), ('role2', False)]

# -----------------------------------------------------------------------------
# DefaultCredentialsCacheHandler Tests
# -----------------------------------------------------------------------------

def test_dach_gca_fails_to_obtain_cache_resolver(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token):
    """
    unit tested:  get_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler
    token = username_password_token

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', None)

    with pytest.raises(GetCachedCredentialsException):
        pdach.get_cached_credentials(token)

def test_dach_gca_fails_to_obtain_cache_key_resolver(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token):
    """
    unit tested:  get_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler
    token = username_password_token

    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', None)

    with pytest.raises(GetCachedCredentialsException):
        pdach.get_cached_credentials(token)

def test_dach_gca_fails_to_locate_cache(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token):
    """
    unit tested:  get_cached_credentials

    test case:
    by default, the MockCredentialsCacheResolver returns None

    """

    pdach = patched_default_credentials_cache_handler
    token = username_password_token

    with pytest.raises(GetCachedCredentialsException):
        pdach.get_cached_credentials(token)


def test_dach_gca_fails_to_locate_cache_key(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_resolver):
    """
    unit tested:  get_cached_credentials

    test case:
    the default pdach fixture uses empty mocks, therefore both the
        get_credentials_cache and get_credentials_cache_key return None

    the patched mock fixtures return values
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    token = username_password_token
    pmacr = patched_mock_credentials_cache_resolver

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    result = pdach.get_cached_credentials(token)

    assert result is None


def test_dach_gca_fails_to_locate_cached_credentials(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_resolver,
        patched_mock_credentials_cache_key_resolver):
    """
    unit tested:  get_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    token = username_password_token
    pmacr = patched_mock_credentials_cache_resolver
    pmackr = patched_mock_credentials_cache_key_resolver
    monkeypatch.setattr(pmackr, 'key', 'user223344')

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', pmackr)

    result = pdach.get_cached_credentials(token)

    assert result is None


def test_dach_gca_succeeds_in_locating_cached_credentials(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_key_resolver):
    """
    unit tested:  get_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    token = username_password_token
    pmackr = patched_mock_credentials_cache_key_resolver

    # DG:  a username is presumably a good key to reference an account:
    key = token.username
    value = MockAccount(account_id='CachedAccount12345')
    pmacr = MockCredentialsCacheResolver(MockCache({key: value}))

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    # key is: 'CachedAccount12345'
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', pmackr)

    result = pdach.get_cached_credentials(token)  # token is ignored by mock

    assert result.account_id == 'CachedAccount12345'

def test_dach_ca_fails_to_obtain_cache_resolver(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, full_mock_account):
    """
    unit tested:  cache_credentials
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account
    token = username_password_token
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', None)

    with pytest.raises(CacheCredentialsException):
        pdach.cache_credentials(authc_token=token, account=account)

def test_dach_ca_fails_to_obtain_cache_key_resolver(
        patched_default_credentials_cache_handler, monkeypatch,
        patched_mock_credentials_cache_resolver,
        username_password_token, full_mock_account):
    """
    unit tested:  cache_credentials

    test case:
    the cache is obtained but the key isn't
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account
    token = username_password_token

    pmacr = patched_mock_credentials_cache_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', None)

    with pytest.raises(CacheCredentialsException):
        pdach.cache_credentials(authc_token=token, account=account)

def test_dach_ca_fails_to_locate_cache(
        patched_default_credentials_cache_handler, full_mock_account,
        username_password_token):
    """
    unit tested:  cache_credentials

    test case:
    by default, the MockCredentialsCacheResolver returns None
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account
    token = username_password_token

    with pytest.raises(CacheCredentialsException):
        pdach.cache_credentials(authc_token=token, account=account)


def test_dach_ca_fails_to_locate_cache_key(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_resolver,
        full_mock_account):
    """
    unit tested:  cache_credentials

    test case:
    the default pdach fixture uses empty mocks, therefore both the
    get_credentials_cache and get_credentials_cache_key return None

    the patched mock fixtures return values
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    account = full_mock_account
    token = username_password_token
    pmacr = patched_mock_credentials_cache_resolver

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    with pytest.raises(CacheCredentialsException):
        pdach.cache_credentials(authc_token=token, account=account)

def test_dach_ca_succeeds_in_caching_account(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_key_resolver,
        patched_mock_credentials_cache_resolver, full_mock_account):
    """
    unit tested:  cache_credentials
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    token = username_password_token
    account = full_mock_account  # has account_id = 8675309

    # pmackr always returns key='user123':
    pmackr = patched_mock_credentials_cache_key_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', pmackr)

    pmacr = patched_mock_credentials_cache_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    pdach.cache_credentials(authc_token=token, account=account)

    # returns a full MockAccount:
    result = pdach.credentials_cache_resolver.cache.get('user123')
    assert result.account_id == 8675309


def test_dach_cca_fails_to_obtain_cache_resolver(
        patched_default_credentials_cache_handler, monkeypatch, full_mock_account):
    """
    unit tested:  clear_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', None)

    with pytest.raises(ClearCacheCredentialsException):
        pdach.clear_cached_credentials(account_id=account.account_id)

def test_dach_cca_fails_to_obtain_cache_key_resolver(
        patched_default_credentials_cache_handler, monkeypatch,
        full_mock_account, patched_mock_credentials_cache_resolver):
    """
    unit tested:  clear_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account

    pmacr = patched_mock_credentials_cache_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', None)

    with pytest.raises(ClearCacheCredentialsException):
        pdach.clear_cached_credentials(account_id=account.account_id)

def test_dach_cca_fails_to_locate_cache(
        patched_default_credentials_cache_handler, full_mock_account,
        username_password_token):
    """
    unit tested:  clear_cached_credentials

    by default, the MockCredentialsCacheResolver returns None
    """

    pdach = patched_default_credentials_cache_handler
    account = full_mock_account

    with pytest.raises(ClearCacheCredentialsException):
        pdach.clear_cached_credentials(account_id=account.account_id)

def test_dach_cca_fails_to_locate_cache_key(
        patched_default_credentials_cache_handler, monkeypatch,
        patched_mock_credentials_cache_resolver, full_mock_account):
    """
    unit tested:  clear_cached_credentials

    test case:
    the default pdach fixture uses empty mocks, therefore both the
    get_credentials_cache and get_credentials_cache_key return None

    the patched mock fixtures return values
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    account = full_mock_account
    pmacr = patched_mock_credentials_cache_resolver

    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    result = pdach.clear_cached_credentials(account_id=account.account_id)

    assert result is None


def test_dach_cca_succeeds_in_removing_cached_credentials(
        patched_default_credentials_cache_handler, monkeypatch,
        username_password_token, patched_mock_credentials_cache_key_resolver,
        patched_mock_credentials_cache_resolver, full_mock_account):
    """
    unit tested:  clear_cached_credentials
    """

    pdach = patched_default_credentials_cache_handler  # doesn't matter if patched
    account = full_mock_account  # has account_id = 8675309

    # pmackr always returns key='user123':
    pmackr = patched_mock_credentials_cache_key_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_key_resolver', pmackr)

    # uses a MockCache:
    pmacr = patched_mock_credentials_cache_resolver
    monkeypatch.setattr(pdach, 'credentials_cache_resolver', pmacr)

    # returns a full MockAccount:
    result = pdach.clear_cached_credentials(account_id=account.account_id)

    assert result.account_id == 8675309
