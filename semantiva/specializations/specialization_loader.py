# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC, abstractmethod
from typing import List, Type
import importlib.metadata
from semantiva.logger import Logger

logger = Logger()


def load_specializations(specs_to_load: str | List[str]):
    """Load specified specializations from the installed packages."""

    if isinstance(specs_to_load, str):
        specs_to_load = [specs_to_load]

    # Get a list of installed packages whitin entry points 'semantiva.specializations'

    installed_packages = importlib.metadata.entry_points(
        group="semantiva.specializations"
    )

    # Keep track of which plugin names we actually find.
    found_specs: set[str] = set()

    for package in installed_packages:
        if package.name in specs_to_load:

            # Load the package and register its components
            semantiva_spec: Type[SemantivaSpecialization] = package.load()
            if not issubclass(semantiva_spec, SemantivaSpecialization):
                logger.warning(
                    "Warning: Specialization %s does not subclass SemantivaSpecialization. Skipping.",
                    package.name,
                )
                continue

            logger.debug("Subscribing %s to ComponentLoader paths", package.name)
            semantiva_spec().register()
            found_specs.add(package.name)
            logger.debug("Subscribed %s to ComponentLoader paths", package.name)

    # Now compare the requested plugins with those actually found
    missing_specs = set(specs_to_load) - found_specs
    for missing in missing_specs:
        logger.warning("Warning: No specialization named '%s' was found.", missing)


class SemantivaSpecialization(ABC):
    """
    Base class that all Semantiva specializations should subclass.
    Provides a uniform interface for registering plugin modules.
    """

    @abstractmethod
    def register(self) -> None:
        """
        Register all modules, paths, etc in ComponentLoader.
        """
        pass
