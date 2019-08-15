# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json

import mock

from sushy.resources import constants as res_cons
from sushy.resources.registry import message_registry
from sushy.resources import settings
from sushy.tests.unit import base


class MessageRegistryTestCase(base.TestCase):

    def setUp(self):
        super(MessageRegistryTestCase, self).setUp()
        self.conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/message_registry.json') as f:
            self.json_doc = json.load(f)

        self.conn.get.return_value.json.return_value = self.json_doc

        self.registry = message_registry.MessageRegistry(
            self.conn, '/redfish/v1/Registries/Test',
            redfish_version='1.0.2')

    def test__parse_attributes(self):
        self.registry._parse_attributes(self.json_doc)
        self.assertEqual('Test.1.1.1', self.registry.identity)
        self.assertEqual('Test Message Registry', self.registry.name)
        self.assertEqual('en', self.registry.language)
        self.assertEqual('This registry defines messages for sushy testing',
                         self.registry.description)
        self.assertEqual('Test', self.registry.registry_prefix)
        self.assertEqual('1.1.1', self.registry.registry_version)
        self.assertEqual('sushy', self.registry.owning_entity)
        self.assertEqual(3, len(self.registry.messages))
        self.assertEqual('Everything OK',
                         self.registry.messages['Success'].description)
        self.assertEqual('Everything done successfully.',
                         self.registry.messages['Success'].message)
        self.assertEqual(res_cons.SEVERITY_OK,
                         self.registry.messages['Success'].severity)
        self.assertEqual(0, self.registry.messages['Success'].number_of_args)
        self.assertEqual(2, len(self.registry.messages['TooBig'].param_types))
        self.assertEqual(res_cons.PARAMTYPE_STRING,
                         self.registry.messages['TooBig'].param_types[0])
        self.assertEqual(res_cons.PARAMTYPE_NUMBER,
                         self.registry.messages['TooBig'].param_types[1])
        self.assertEqual('Panic', self.registry.messages['Failed'].resolution)

    def test__parse_attribtues_unknown_param_type(self):
        self.registry.json['Messages']['Failed']['ParamTypes'] = \
            ['unknown_type']
        self.assertRaisesRegex(KeyError,
                               'unknown_type',
                               self.registry._parse_attributes, self.json_doc)

    def test_parse_message(self):
        conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/message_registry.json') as f:
            conn.get.return_value.json.return_value = json.load(f)
        registry = message_registry.MessageRegistry(
            conn, '/redfish/v1/Registries/Test',
            redfish_version='1.0.2')
        registries = {'Test.1.0.0': registry}
        message_field = settings.MessageListField('Foo')
        message_field.message_id = 'Test.1.0.0.TooBig'
        message_field.message_args = ['arg1', 10]
        message_field.severity = None
        message_field.resolution = None

        parsed_msg = message_registry.parse_message(registries, message_field)

        self.assertEqual('Try again', parsed_msg.resolution)
        self.assertEqual(res_cons.SEVERITY_WARNING, parsed_msg.severity)
        self.assertEqual('Property\'s arg1 value cannot be greater than 10.',
                         parsed_msg.message)

    def test_parse_message_with_severity_resolution_no_args(self):
        conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/message_registry.json') as f:
            conn.get.return_value.json.return_value = json.load(f)
        registry = message_registry.MessageRegistry(
            conn, '/redfish/v1/Registries/Test',
            redfish_version='1.0.2')
        registries = {'Test.1.0.0': registry}
        message_field = settings.MessageListField('Foo')
        message_field.message_id = 'Test.1.0.0.Success'
        message_field.severity = res_cons.SEVERITY_OK
        message_field.resolution = 'Do nothing'

        parsed_msg = message_registry.parse_message(registries, message_field)

        self.assertEqual('Do nothing', parsed_msg.resolution)
        self.assertEqual(res_cons.SEVERITY_OK, parsed_msg.severity)
        self.assertEqual('Everything done successfully.',
                         parsed_msg.message)
