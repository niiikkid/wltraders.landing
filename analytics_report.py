#!/usr/bin/env python3
"""Print unique human/bot counters and the latest recorded visits."""
import json
from analytics_server import summary

print(json.dumps(summary(), ensure_ascii=False, indent=2))
