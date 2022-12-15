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

"""VPC-SC Demo Server."""

import logging

from flask import Flask
from frontend_blueprint import frontend
from session_blueprint import session


def configure_logging():
    """Set up logging for webserver."""
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.INFO)


def create_app():
    """Create the webserver, register blueprints."""
    curr_app = Flask(__name__)
    curr_app.register_blueprint(frontend)
    curr_app.register_blueprint(session)
    configure_logging()
    return curr_app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    app.run()
