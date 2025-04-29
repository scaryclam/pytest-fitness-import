import ast
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path

import pytest


@dataclass
class FitnessReport:
    warnings: dict = field(default_factory=dict)
    total_count: int = 0


@dataclass
class FitnessConfig:
    warning_configs: dict = field(default_factory=dict)


class Fitness:
    report = None
    config = None

    def __init__(self, config):
        self.config = config

    def pytest_sessionstart(self, session):
        self.report = FitnessReport()
        self.session_failed = False
        self.allowed_warnings = self.config.warning_configs

    def pytest_sessionfinish(self, session, exitstatus):
        for package, config in self.config.warning_configs.items():
            self._make_checks(session, package, config)

    def _make_checks(self, session, package, config):
        path_components = ['.'] + package.split('.')
        base_path = os.path.join(*path_components)
        python_files = []  # This is a list of files to check

        for found_file in Path('.').rglob("*.py"):
            if "migrations" not in str(found_file):
                python_files.append(found_file)

        check_results = {}
        for file_path in python_files:
            with open(file_path, encoding="utf-8") as current_fd:
                tree = ast.parse(current_fd.read(), filename=str(file_path))
                check_results[current_fd.name] = {
                    'errors': 0
                    'details': []
                }

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for package_name in 
                            if any(
                                alias.name.startswith(pkg) for pkg in RESTRICTED_PACKAGES
                            ):
                                detail_message = f"FOUND IMPORT in {current_fd.name} LINE {node.lineno}"
                                print(detail_message)
                                check_results[current_fd.name]['errors'] += 1
                                check_results[current_fd.name]['details'].append(detail_message)
                    elif isinstance(node, ast.ImportFrom):
                        detail_message = f"FOUND IMPORT FROM in {current_fd.name} LINE {node.lineno}"
                        print(detail_message)
                        check_results[current_fd.name]['errors'] += 1
                        check_results[current_fd.name]['details'].append(detail_message)

        return check_results

    def pytest_terminal_summary(self, terminalreporter):
        BOLD = "\033[1m"
        RED = "\033[91m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        END = "\033[0m"

        terminalreporter.ensure_newline()
        title = "fitness report summary"
        terminal_kwargs = {"bold": True}
        if self.session_failed:
            title += " (failed)"
            terminal_kwargs["red"] = True
        else:
            title += " (passed)"
            terminal_kwargs["green"] = True
        terminalreporter.section(title, sep="=", **terminal_kwargs)

        content = []
        if self.report.warnings == {}:
            terminalreporter.line(
                "No warnings to report on. Use fitness_warnings in pyproject.toml for configure some",
                green=True,
            )

        for warning_name, warning_data in self.report.warnings.items():
            message = (
                f"{warning_name}: {BOLD}Had {warning_data['count']} occurrences{END}"
            )
            if warning_data.get("result") == "fail":
                message += f"{RED}{BOLD}, was allowed {warning_data['config']['allowed_number']}{END}"
                terminalreporter.line(message, red=True)
            if warning_data.get("result") == "report":
                terminalreporter.line(message, blue=True)
            if warning_data.get("result") == "success":
                message += f"{GREEN}{BOLD}, is allowed {warning_data['config']['allowed_number']}{END}"
                terminalreporter.line(message, green=True)

        terminalreporter.line(os.linesep.join(content))


def pytest_addoption(parser):
    group = parser.getgroup("fitness-import-pytest")
    group.addoption(
        "--use-fitness-import", action="store_true", help="Whether to use fitness import or not"
    )


def pytest_configure(config):
    if not config.getoption("use_fitness_import"):
        return

    ini_config = config.inicfg.get("fitness_warnings", [])
    warning_dict = {}
    for warning_config in ini_config:
        target_package = warning_config['target_package']
        restriction_type = warning_config.get('type', 'all')
        exceptions = warning_config.get('exceptions', [])
        warning_dict[target_package] = {"restriction_type": restriction_type, "exceptions": exceptions}

    fitness_config = FitnessConfig(warning_configs=warning_dict)
    config.pluginmanager.register(Fitness(fitness_config))

