import enumarg

PURGE_AUTO_ADD_NEVER = 0
PURGE_AUTO_ADD_ON_ERROR = 1
PURGE_AUTO_ADD_ALWAYS = 2

purge_auto_add_enum_arg_table = enumarg.EnumArgTable({
    "never": PURGE_AUTO_ADD_NEVER,
    "onerror": PURGE_AUTO_ADD_ON_ERROR,
    "always": PURGE_AUTO_ADD_ALWAYS
})

class WbzSettings:
    __slots__ = ("purge_auto_add", "ignore_auto_add_missing_files", "debug_manual_auto_add")

    def __init__(self, purge_auto_add_str, ignore_auto_add_missing_files, debug_manual_auto_add):
        self.purge_auto_add = purge_auto_add_enum_arg_table.parse_enum_arg(purge_auto_add_str, "Unknown purge-auto-add value \"{}\"!")
        self.ignore_auto_add_missing_files = ignore_auto_add_missing_files
        self.debug_manual_auto_add = debug_manual_auto_add
