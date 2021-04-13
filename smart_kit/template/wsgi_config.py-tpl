#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

bind = '0.0.0.0:8000'
workers = os.cpu_count() * 2 + 1
preload_app = True


# Server Hooks
def on_starting(server):
    print("SERVER STARTING...")
