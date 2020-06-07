from math import ceil
from unittest.mock import patch

from requests import RequestException
import requests_mock
from packaging.version import Version as Pep440Version

from django.test import TestCase

from allianceauth.templatetags.admin_status import (
    status_overview,
    _fetch_list_from_gitlab,
    _current_notifications, 
    _current_version_summary, 
    _fetch_notification_issues_from_gitlab,
    _fetch_tags_from_gitlab,
    _latests_versions
)

MODULE_PATH = 'allianceauth.templatetags'


def create_tags_list(tag_names: list):
    return [{'name': str(tag_name)} for tag_name in tag_names]


GITHUB_TAGS = create_tags_list(['v2.4.6a1', 'v2.4.5', 'v2.4.0', 'v2.0.0', 'v1.1.1'])
GITHUB_NOTIFICATION_ISSUES = [
    {
        'id': 1,
        'title': 'first issue'
    },
    {
        'id': 2,
        'title': 'second issue'
    },
    {
        'id': 3,
        'title': 'third issue'
    },
    {
        'id': 4,
        'title': 'forth issue'
    },
    {
        'id': 5,
        'title': 'fifth issue'
    },
    {
        'id': 6,
        'title': 'sixth issue'
    },
]
TEST_VERSION = '2.6.5'


class TestStatusOverviewTag(TestCase):

    @patch(MODULE_PATH + '.admin_status.__version__', TEST_VERSION)
    @patch(MODULE_PATH + '.admin_status._fetch_celery_queue_length')
    @patch(MODULE_PATH + '.admin_status._current_version_summary')
    @patch(MODULE_PATH + '.admin_status._current_notifications')    
    def test_status_overview(
        self, 
        mock_current_notifications, 
        mock_current_version_info,
        mock_fetch_celery_queue_length
    ):
        notifications = {
            'notifications': GITHUB_NOTIFICATION_ISSUES[:5]
        }
        mock_current_notifications.return_value = notifications
            
        version_info = {
            'latest_major': True,
            'latest_minor': True,
            'latest_patch': True,
            'current_version': TEST_VERSION,
            'latest_major_version': '2.0.0',
            'latest_minor_version': '2.4.0',
            'latest_patch_version': '2.4.5',
        }
        mock_current_version_info.return_value = version_info
        mock_fetch_celery_queue_length.return_value = 3
        
        context = {}
        result = status_overview(context)
        expected = {
            'notifications': GITHUB_NOTIFICATION_ISSUES[:5],
            'latest_major': True,
            'latest_minor': True,
            'latest_patch': True,
            'current_version': TEST_VERSION,
            'latest_major_version': '2.0.0',
            'latest_minor_version': '2.4.0',
            'latest_patch_version': '2.4.5',
            'task_queue_length': 3,
        }
        self.assertEqual(result, expected)


class TestNotifications(TestCase):

    @requests_mock.mock()
    def test_fetch_notification_issues_from_gitlab(self, requests_mocker):
        url = (
            'https://gitlab.com/api/v4/projects/allianceauth%2Fallianceauth/issues'
            '?labels=announcement'
        )        
        requests_mocker.get(url, json=GITHUB_NOTIFICATION_ISSUES)
        result = _fetch_notification_issues_from_gitlab()
        self.assertEqual(result, GITHUB_NOTIFICATION_ISSUES)

    @patch(MODULE_PATH + '.admin_status.cache')
    def test_current_notifications_normal(self, mock_cache):
        mock_cache.get_or_set.return_value = GITHUB_NOTIFICATION_ISSUES

        result = _current_notifications()
        self.assertEqual(result['notifications'], GITHUB_NOTIFICATION_ISSUES[:5])

    @patch(MODULE_PATH + '.admin_status.cache')
    def test_current_notifications_failed(self, mock_cache):
        mock_cache.get_or_set.side_effect = RequestException

        result = _current_notifications()
        self.assertEqual(result['notifications'], list())


class TestCeleryQueueLength(TestCase):

    def test_get_celery_queue_length(self):
        pass


class TestVersionTags(TestCase):

    @patch(MODULE_PATH + '.admin_status.__version__', TEST_VERSION)
    @patch(MODULE_PATH + '.admin_status.cache')
    def test_current_version_info_normal(self, mock_cache):
        mock_cache.get_or_set.return_value = GITHUB_TAGS

        result = _current_version_summary()
        self.assertTrue(result['latest_major'])
        self.assertTrue(result['latest_minor'])
        self.assertTrue(result['latest_patch'])
        self.assertEqual(result['latest_major_version'], '2.0.0')
        self.assertEqual(result['latest_minor_version'], '2.4.0')
        self.assertEqual(result['latest_patch_version'], '2.4.5')

    @patch(MODULE_PATH + '.admin_status.__version__', TEST_VERSION)
    @patch(MODULE_PATH + '.admin_status.cache')
    def test_current_version_info_failed(self, mock_cache):
        mock_cache.get_or_set.side_effect = RequestException
        
        expected = {}
        result = _current_version_summary()
        self.assertEqual(result, expected)

    @requests_mock.mock()
    def test_fetch_tags_from_gitlab(self, requests_mocker):
        url = (
            'https://gitlab.com/api/v4/projects/allianceauth%2Fallianceauth'
            '/repository/tags'
        )        
        requests_mocker.get(url, json=GITHUB_TAGS)
        result = _fetch_tags_from_gitlab()
        self.assertEqual(result, GITHUB_TAGS)


class TestLatestsVersion(TestCase):

    def test_all_version_types_defined(self):
        
        tags = create_tags_list(
            ['2.1.1', '2.1.0', '2.0.0', '2.1.1a1', '1.1.1', '1.1.0', '1.0.0']
        )
        major, minor, patch = _latests_versions(tags)
        self.assertEqual(major, Pep440Version('2.0.0'))
        self.assertEqual(minor, Pep440Version('2.1.0'))
        self.assertEqual(patch, Pep440Version('2.1.1'))

    def test_major_and_minor_not_defined_with_zero(self):
        
        tags = create_tags_list(
            ['2.1.2', '2.1.1', '2.0.1', '2.1.1a1', '1.1.1', '1.1.0', '1.0.0']
        )
        major, minor, patch = _latests_versions(tags)
        self.assertEqual(major, Pep440Version('2.0.1'))
        self.assertEqual(minor, Pep440Version('2.1.1'))
        self.assertEqual(patch, Pep440Version('2.1.2'))
        
    def test_can_ignore_invalid_versions(self):
        
        tags = create_tags_list(
            ['2.1.1', '2.1.0', '2.0.0', '2.1.1a1', 'invalid']
        )
        major, minor, patch = _latests_versions(tags)
        self.assertEqual(major, Pep440Version('2.0.0'))
        self.assertEqual(minor, Pep440Version('2.1.0'))
        self.assertEqual(patch, Pep440Version('2.1.1'))


class TestFetchListFromGitlab(TestCase):
   
    page_size = 2
    
    def setUp(self):
        self.url = (
            'https://gitlab.com/api/v4/projects/allianceauth%2Fallianceauth'
            '/repository/tags'
        )

    @classmethod
    def my_callback(cls, request, context):
        page = int(request.qs['page'][0])
        start = (page - 1) * cls.page_size
        end = start + cls.page_size
        return GITHUB_TAGS[start:end]        
    
    @requests_mock.mock()
    def test_can_fetch_one_page_with_header(self, requests_mocker):
        headers = {
            'x-total-pages': '1'
        }
        requests_mocker.get(self.url, json=GITHUB_TAGS, headers=headers)
        result = _fetch_list_from_gitlab(self.url)
        self.assertEqual(result, GITHUB_TAGS)
        self.assertEqual(requests_mocker.call_count, 1)

    @requests_mock.mock()
    def test_can_fetch_one_page_wo_header(self, requests_mocker):        
        requests_mocker.get(self.url, json=GITHUB_TAGS)
        result = _fetch_list_from_gitlab(self.url)
        self.assertEqual(result, GITHUB_TAGS)
        self.assertEqual(requests_mocker.call_count, 1)

    @requests_mock.mock()
    def test_can_fetch_one_page_and_ignore_invalid_header(self, requests_mocker):
        headers = {
            'x-total-pages': 'invalid'
        }
        requests_mocker.get(self.url, json=GITHUB_TAGS, headers=headers)
        result = _fetch_list_from_gitlab(self.url)
        self.assertEqual(result, GITHUB_TAGS)
        self.assertEqual(requests_mocker.call_count, 1)

    @requests_mock.mock()
    def test_can_fetch_multiple_pages(self, requests_mocker):     
        total_pages = ceil(len(GITHUB_TAGS) / self.page_size)
        headers = {
            'x-total-pages': str(total_pages)
        }
        requests_mocker.get(self.url, json=self.my_callback, headers=headers)
        result = _fetch_list_from_gitlab(self.url)
        self.assertEqual(result, GITHUB_TAGS)
        self.assertEqual(requests_mocker.call_count, total_pages)

    @requests_mock.mock()
    def test_can_fetch_given_number_of_pages_only(self, requests_mocker):     
        total_pages = ceil(len(GITHUB_TAGS) / self.page_size)
        headers = {
            'x-total-pages': str(total_pages)
        }
        requests_mocker.get(self.url, json=self.my_callback, headers=headers)
        max_pages = 2
        result = _fetch_list_from_gitlab(self.url, max_pages=max_pages)
        self.assertEqual(result, GITHUB_TAGS[:4])
        self.assertEqual(requests_mocker.call_count, max_pages)