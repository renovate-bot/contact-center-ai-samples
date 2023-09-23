# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""setup.py calls the DIalogflow API to setup a webhook sample"""

import argparse
import json
import logging
import sys
import time
import uuid

from typing import Optional, Dict

import google.auth
from google.cloud.dialogflowcx_v3 import (
    Agent,
    AgentsClient,
    FlowsClient,
    SessionsClient,
    DetectIntentRequest,
    QueryInput,
    TextInput,
    QueryParameters,
)
from proto.marshal.collections import MapComposite

DEFAULT_LOCATION = 'global'
DEFAULT_AGENT_LANG_CODE = 'en'
DEFAULT_AGENT_DISPLAY_NAME = 'Long Session sample'
DEFAULT_AGENT_TIME_ZONE = 'America/Los_Angeles'
PAGE_NAME = 'Long session sample page'

logging.getLogger().setLevel(logging.INFO)


# Create a function that can marshal the current state of the session to json:
def marshal_session(response, as_dict=True):
  session_restart_data = {'current_page_name': response.query_result.current_page.name, 'parameters':response.query_result.parameters}

  def default(obj):
      if isinstance(obj, MapComposite): return dict(obj)
      raise TypeError()

  session_str = json.dumps(session_restart_data, default=default)
  return json.loads(session_str) if as_dict else session_str


class Setup:
    '''Setup configures a Dialogflow CX agent for the long session sample'''
    def __init__(self, args):
        '''Gets Dialogflow agent, clients and auth'''
        _, project_id = google.auth.default()
        self.project_id = project_id
        self.args = args

        client_options = {
            "api_endpoint": f'{self.args.location}-dialogflow.googleapis.com'
        }
        self.agents_client = AgentsClient(client_options=client_options)
        self.sessions_client = SessionsClient(client_options=client_options)
        self.flows_client = FlowsClient(client_options=client_options)

        # Create or get Dialogflow CX agent.
        if not self.args.agent_id:
            self.agent = self.create_agent()
        else:
            self.agent = self.get_agent()

    def run(self):
        '''Sets up a Dialogflow CX agent and runs the sample.'''
        self.setup_agent()

        parameters = {"first_name": 'John', 'last_name':'Doe'}
        response = self.detect_intent('Hello', session_state={'parameters':parameters})

        session_state = marshal_session(response)
        response = self.detect_intent('Hello much later', session_state=session_state)

    def detect_intent(self, intent_text, session_state=None, override_session_state_parameters: Optional[Dict]=None):

        if session_state is None:
            session_state = {}
        
        parameters = session_state.get('parameters', {})
        if override_session_state_parameters:
            parameters.update(override_session_state_parameters)

        parameters_struct = google.protobuf.struct_pb2.Struct()
        parameters_struct.update(parameters)

        # Unmarshal the saved state:
        current_page = session_state.get('current_page_name')
        query_params = QueryParameters(current_page=current_page, parameters=parameters_struct)

        session_id = str(uuid.uuid1())
        request = DetectIntentRequest(session=f'projects/{self.project_id}/locations/global/agents/2f70a60e-13a0-4736-99cf-a03d8c16d7ec/sessions/{session_id}', 
                                        query_input=QueryInput(language_code='en', 
                                                                text=TextInput(text=intent_text)),
                                        query_params=query_params)
        return self.sessions_client.detect_intent(request)


    # def dump_state(self, delay=0):

    #     # Newly created agents might need a short delay to become stable.
    #     if delay:
    #         time.sleep(delay)

    #     # Create example parameters:
    #     parameters = google.protobuf.struct_pb2.Struct()
    #     parameters.update({"first_name": 'John', 'last_name':'Doe'})

    #     # Marshal the current state:
    #     session_id = str(uuid.uuid1())
    #     request = DetectIntentRequest(session=f'projects/{self.project_id}/locations/global/agents/2f70a60e-13a0-4736-99cf-a03d8c16d7ec/sessions/{session_id}', 
    #                                     query_input=QueryInput(language_code='en', 
    #                                                             text=TextInput(text='Hello')),
    #                                     query_params=QueryParameters(parameters=parameters))
    #     response = self.sessions_client.detect_intent(request)
    #     return marshal_session(response)





    #     # Create a test interaction, to confirm the webhook works as-intended:
    #     text_response = ResponseMessage.Text(text=['Entering example_page', 'Webhook received: go to example_page (Tag: webhook-tag)'])
    #     virtual_agent_output = ConversationTurn.VirtualAgentOutput(current_page=self.page, triggered_intent=self.intent, text_responses=[text_response])
    #     conversation_turn = ConversationTurn(virtual_agent_output=virtual_agent_output, user_input=ConversationTurn.UserInput(is_webhook_enabled=True, input=QueryInput(text=TextInput(text=f'go to {PAGE_NAME}'))))
    #     test_case = self.test_cases_client.create_test_case(parent=self.agent.name, test_case=TestCase(display_name=TEST_CASE_DISPLAY_NAME, 
    #                         test_case_conversation_turns=[conversation_turn],
    #                         test_config=TestConfig(flow=self.agent.start_flow)))
    #     print(self.agent.start_flow)

    #     lro = self.test_cases_client.run_test_case(request=RunTestCaseRequest(name=test_case.name))
    #     while lro.running():
    #         time.sleep(1)
    #     assert lro.result().result.test_result == TestResult.PASSED
    #     print('Test successful!')

    def create_agent(self):
        '''Creates a agent'''
        parent = f'projects/{self.project_id}/locations/{self.args.location}'
        agent = Agent(
            display_name=self.args.agent_display_name,
            default_language_code=self.args.agent_default_lang_code,
            time_zone=self.args.agent_time_zone,
        )
        request = {"agent": agent, "parent": parent}
        return self.agents_client.create_agent(request=request)

    def get_agent(self):
        '''Gets an existing agent.'''
        parent = f'projects/{self.project_id}/locations/{self.args.location}'
        return self.agents_client.get_agent(request={"parent": parent})

    def setup_agent(self):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Setup Dialogflow CX webhook sample')
    parser.add_argument(
        '--location',
        help='Google Cloud location or region to create/use Dialogflow CX in',
        default=DEFAULT_LOCATION)
    parser.add_argument(
        '--agent-id',
        help='ID of the Dialogflow CX agent')
    parser.add_argument(
        '--agent-default-lang-code',
        help='Default language code of the Dialogflow CX agent',
        default=DEFAULT_AGENT_LANG_CODE)
    parser.add_argument(
        '--agent-display-name',
        help='Display name of the Dialogflow CX agent',
        default=DEFAULT_AGENT_DISPLAY_NAME)
    parser.add_argument(
        '--agent-time-zone',
        help='Time zone of the Dialogflow CX agent',
        default=DEFAULT_AGENT_TIME_ZONE)
    main = Setup(args=parser.parse_args())
    sys.exit(main.run())
