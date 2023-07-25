import re

release_name_regex = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")

bool_check = ((lambda x: isinstance(x, bool)), "is not a boolean (true/false).")
str_check = ((lambda x: isinstance(x, str)), "is not a string.")
int_list_check = ((lambda x: isinstance(x, list) and all(isinstance(y, int) for y in x)), "is not a list of integers.")

test_and_release_options_format = {
    "dolphin-lua-core-dirname": str_check,
    "release-name": ((lambda x: isinstance(x, str) and release_name_regex.match(x) is not None), "is not a valid release name (format vN.N.N, where N is a number)"),
    "for-gui": bool_check,
    "include-tests": int_list_check,
    "exclude-tests": int_list_check,
    "rmce01-iso": str_check,
    "rmcp01-iso": str_check,
    "rmcj01-iso": str_check,
    "rmck01-iso": str_check,
    "test-release": bool_check,
    "release-clean-install": ((lambda x: x in {True, False, "random"}), "is not of true, false, or random."),
    "iso-directory": str_check,
    "sevenz-filename": str_check,
    "storage-folder-absolute": str_check,
    "storage-folder-relative": str_check,
    "storage-folder-relative-no-parent": str_check,
    "dolphin-folder-absolute": str_check,
    "dolphin-folder-relative": str_check,
    "dolphin-folder-relative-no-parent": str_check,
    "temp-folder-relative": str_check,
    "temp-folder-absolute": str_check,
    "temp-folder-relative-no-parent": str_check,
    "wiimm-folder-absolute": str_check,
    "wiimm-folder-relative": str_check,
    "wiimm-folder-relative-no-parent": str_check,
    "extra-hq-textures-folder-relative-no-parent": str_check,
    "chadsoft-cache-folder-relative": str_check
    "chadsoft-cache-folder-relative-no-parent": str_check
}

expected_option_names = set(test_and_release_options_format.keys())

def open_options(options_filename):
    with open(options_filename, "r") as f:
        options = yaml.safe_load(f)

    actual_option_names = set(options.keys())

    missing_option_names = expected_option_names - actual_option_names

    if len(missing_option_names) != 0:
        raise RuntimeError(f"test_and_release_options file {options_filename} is missing the following options: " + ", ".join(f'"{x}"' for x in missing_option_names))

    option_format_errors = []

    for option_name, option_value in options.items():
        option_format_check, option_format_error_message = test_and_release_options_format[option_name]
        if not option_format_check(option_value):
            option_format_errors.append(f"Option \"{option_name}\" {option_format_error_message}")

    if len(option_format_errors) != 0:
        raise RuntimeError("\n".join(option_format_errors))

    return options
