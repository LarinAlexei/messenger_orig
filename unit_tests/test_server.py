import sys
import os
import unittest
from server import process_client_msg

sys.path.insert(0, os.path.join(os.getcwd(), '..'))

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, ENCODING, PRESENCE, ERROR, TIME, USER


class TestServer(unittest.TestCase):
    ok_dict = {
        RESPONSE: 200,
    }

    err_dict = {
        RESPONSE: 400,
        ERROR: 'Bad request'
    }

    def test_ok_check(self):
        self.assertEqual(
            process_client_msg(
                {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Larin'}}
            ), self.ok_dict
        )

    def test_no_action(self):
        self.assertEqual(
            process_client_msg(
                {TIME: 1.1, USER: {ACCOUNT_NAME: 'Larin'}}
            ), self.err_dict
        )

    def test_no_time(self):
        self.assertEqual(
            process_client_msg(
                {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Larin'}}
            ), self.err_dict
        )

    def test_wrong_action(self):
        self.assertEqual(
            process_client_msg(
                {ACTION: 'no action', TIME: 1.1, USER: {ACCOUNT_NAME: 'Larin'}}
            ), self.err_dict
        )

    def test_account_name(self):
        self.assertEqual(
            process_client_msg(
                {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Bad name'}}
            ), self.err_dict
        )

    def test_response_dict(self):
        self.assertIsInstance(
            process_client_msg(
                {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Larin'}}
            ), dict
        )
        self.assertIsInstance(
            process_client_msg(
                {ACTION: PRESENCE, }
            ), dict
        )

    def test_response_empty_param(self):
        with self.assertRaises(TypeError):
            process_client_msg()


if __name__ == '__main__':
    unittest.main()
