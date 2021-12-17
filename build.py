#!/usr/bin/env python

import subprocess as sp

if __name__ == "__main__":
    sp.Popen(["cargo","build"]).wait()
    sp.Popen(["./target/debug/codeScraper","get","1613","-d","./tmp"]).wait()