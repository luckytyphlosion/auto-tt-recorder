# =============================================================================
# Copyright (c) 2022 luckytyphlosion
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
# =============================================================================

import subprocess
import time

def main():

    try:
        popen = subprocess.Popen(("../dolphin/DolphinR.exe"), encoding="utf-8")

        while True:
            returncode = popen.poll()
            # dolphin exited normally
            if returncode is not None:
                break
    
            # some abnormal condition, implement later
            if False:
                popen.terminate()
                break

            time.sleep(1)
    except KeyboardInterrupt as e:
        popen.terminate()
        raise RuntimeError(e)

if __name__ == "__main__":
    main()
