import sublime
import sublime_plugin

from .common import (
    SETTINGS_FILE_BASENAME,
    SETTINGS_KEY_COMMIT_SKIPPING_MODE,
    SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE,
)


class BlameSetCommitSkippingMode(sublime_plugin.TextCommand):
    MODE_NONE = False
    MODE_SAME_FILE_SAME_COMMIT = "same_file_same_commit"
    MODE_CROSS_FILE_SAME_COMMIT = "cross_file_same_commit"
    MODE_CROSS_ANY_FILE = "cross_any_file"
    MODE_CROSS_ANY_HISTORICAL_FILE = "cross_any_historical_file"

    METADATA = {
        MODE_NONE: {"elaboration": "<Disable Skipping>", "git_args": []},
        MODE_SAME_FILE_SAME_COMMIT: {
            "elaboration": "... moved/copied the line within a file",
            "git_args": ["-M"],
        },
        MODE_CROSS_FILE_SAME_COMMIT: {
            "elaboration": "... moved/copied the line from another file modified in the same commit",
            "git_args": ["-C"],
        },
        MODE_CROSS_ANY_FILE: {
            "elaboration": "... created the file with a copy of a line from any other file",
            "git_args": ["-C"] * 2,
        },
        MODE_CROSS_ANY_HISTORICAL_FILE: {
            "elaboration": "... created the file with a copy of a line from any other historical file",
            "git_args": ["-C"] * 3,
        },
    }

    def run(self, edit, mode, permanence):
        if permanence:
            sublime.load_settings(SETTINGS_FILE_BASENAME).set(
                SETTINGS_KEY_COMMIT_SKIPPING_MODE, mode
            )
            sublime.save_settings(SETTINGS_FILE_BASENAME)
            self.view.settings().erase(SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE)
        else:
            self.view.settings().set(SETTINGS_KEY_TEMPORARY_COMMIT_SKIPPING_MODE, mode)

    def input(self, args):  # noqa: A003
        return ModeInputHandler()


# @todo #21 Since we now use *InputHandlers, make a PR to package_control_channel to bump the minimum required sublime build to 3170 https://github.com/wbond/package_control_channel/blob/master/repository/g.json


class ModeInputHandler(sublime_plugin.ListInputHandler):
    def placeholder(self):
        return "Select a mode"

    # @todo #21 When presenting commit-skipping modes in the Command Palette, preselect the one currently in effect
    def list_items(self):
        return [
            [metadata["elaboration"], mode]
            if mode == BlameSetCommitSkippingMode.MODE_NONE
            else [
                "{0} (git blame {1})".format(
                    metadata["elaboration"], " ".join(metadata["git_args"])
                ),
                mode,
            ]
            for mode, metadata in BlameSetCommitSkippingMode.METADATA.items()
        ]

    def next_input(self, args):
        return PermanenceInputHandler()

    def description(self, value, text):
        return 'to "{0}"'.format(text)


class PermanenceInputHandler(sublime_plugin.ListInputHandler):
    def list_items(self):
        return [
            ("Temporarily (for this open file)", False),
            ("Permanently (a new default will be written to the settings file)", True),
        ]
